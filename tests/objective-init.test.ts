/**
 * Tests for book-idea-manager: slug normalization, folder creation, state bootstrap.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import {
  normalizeSlug,
  createBookIdea,
  listBookIdeaSlugs,
} from '../src/lib/book-idea-manager.js';

let tmpDir: string;

beforeEach(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-test-'));
});

afterEach(async () => {
  await fs.remove(tmpDir);
});

describe('normalizeSlug', () => {
  it('lowercases and replaces spaces with hyphens', () => {
    expect(normalizeSlug('My Book Title')).toBe('my-book-title');
  });

  it('strips special characters', () => {
    expect(normalizeSlug('Book: The "Real" Story!')).toBe('book-the-real-story');
  });

  it('collapses multiple hyphens', () => {
    expect(normalizeSlug('book--title')).toBe('book-title');
  });

  it('trims leading and trailing hyphens', () => {
    expect(normalizeSlug('--book title--')).toBe('book-title');
  });

  it('returns empty string for purely special-char input', () => {
    expect(normalizeSlug('!!!')).toBe('');
  });
});

describe('createBookIdea', () => {
  it('creates spec folder with assets/ and content folder with chapters/ at repo root', async () => {
    const { folder, bookContentDir } = await createBookIdea(tmpDir, 'My Test Book', 'sequential');
    expect(await fs.pathExists(path.join(folder, 'assets'))).toBe(true);
    expect(await fs.pathExists(path.join(bookContentDir, 'chapters'))).toBe(true);
    // spec folder must NOT contain a book/ directory
    expect(await fs.pathExists(path.join(folder, 'book'))).toBe(false);
  });

  it('writes a valid state.json', async () => {
    const { state } = await createBookIdea(tmpDir, 'My Test Book', 'sequential');
    expect(state.sanitizedBookIdeaName).toBe('my-test-book');
    expect(state.initialized).toBe(true);
    expect(state.finalized).toBe(false);
    expect(state.currentStage).toBe('1-book-init');
    expect(state.orchestrationMode).toBe('sequential');
  });

  it('sets parallel mode when specified', async () => {
    const { state } = await createBookIdea(tmpDir, 'Parallel Book', 'parallel');
    expect(state.orchestrationMode).toBe('parallel');
  });
});

describe('listBookIdeaSlugs', () => {
  it('returns empty array when .spec/ does not exist', async () => {
    const slugs = await listBookIdeaSlugs(tmpDir);
    expect(slugs).toEqual([]);
  });

  it('lists slugs from .spec/ subdirectories', async () => {
    await fs.ensureDir(path.join(tmpDir, '.spec', 'my-book'));
    await fs.ensureDir(path.join(tmpDir, '.spec', 'another-book'));
    const slugs = await listBookIdeaSlugs(tmpDir);
    expect(slugs).toContain('my-book');
    expect(slugs).toContain('another-book');
    expect(slugs.length).toBe(2);
  });
});
