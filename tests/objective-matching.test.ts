/**
 * Tests for book-idea matching: exact, close, and no-match scenarios.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import { findBookIdeaMatch } from '../src/lib/book-idea-manager.js';

let tmpDir: string;

beforeEach(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-match-'));
});

afterEach(async () => {
  await fs.remove(tmpDir);
});

async function seedBookIdeas(...slugs: string[]): Promise<void> {
  for (const slug of slugs) {
    await fs.ensureDir(path.join(tmpDir, '.spec', slug));
  }
}

describe('findBookIdeaMatch', () => {
  it('returns kind=none when .spec/ is empty', async () => {
    const result = await findBookIdeaMatch(tmpDir, 'my-book');
    expect(result.kind).toBe('none');
  });

  it('returns kind=exact on exact slug match', async () => {
    await seedBookIdeas('my-book');
    const result = await findBookIdeaMatch(tmpDir, 'my-book');
    expect(result.kind).toBe('exact');
    expect(result.slug).toBe('my-book');
  });

  it('returns kind=close for Levenshtein distance ≤ 2', async () => {
    await seedBookIdeas('my-book');
    // 'my-boo' is distance 1 from 'my-book'
    const result = await findBookIdeaMatch(tmpDir, 'my-boo');
    expect(result.kind).toBe('close');
    if (result.kind === 'close') {
      expect(result.suggestion).toBe('my-book');
    }
  });

  it('returns kind=close for substring containment', async () => {
    await seedBookIdeas('my-amazing-book');
    const result = await findBookIdeaMatch(tmpDir, 'amazing-book');
    expect(result.kind).toBe('close');
  });

  it('returns kind=none for unrelated slugs', async () => {
    await seedBookIdeas('cooking-guide', 'travel-diary');
    const result = await findBookIdeaMatch(tmpDir, 'quantum-physics');
    expect(result.kind).toBe('none');
  });

  it('does not return a close match for distance > 2', async () => {
    await seedBookIdeas('completely-different');
    const result = await findBookIdeaMatch(tmpDir, 'abc');
    expect(result.kind).toBe('none');
  });
});
