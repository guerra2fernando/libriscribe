/**
 * Tests for state-manager: read, write, patch, markStageComplete, stateExists.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import {
  writeState,
  readState,
  patchState,
  markStageComplete,
  stateExists,
} from '../src/lib/state-manager.js';
import type { BookIdeaState } from '../src/lib/types.js';

let tmpDir: string;

const baseState: BookIdeaState = {
  bookIdeaName: 'Test Book',
  sanitizedBookIdeaName: 'test-book',
  bookIdeaMemoryFolder: '.spec/test-book',
  bookContentDir: 'test-book',
  currentStage: '1-book-init',
  completedSteps: [],
  incompletedStages: [],
  nextRecommendedStep: '1-book-init',
  lastUpdatedBy: 'test',
  lastUpdatedAt: '2026-01-01T00:00:00Z',
  initialized: true,
  finalized: false,
  orchestrationMode: 'sequential',
  chapterCount: 0,
  manuscriptFile: null,
};

beforeEach(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-state-'));
});

afterEach(async () => {
  await fs.remove(tmpDir);
});

describe('stateExists', () => {
  it('returns false when state.json does not exist', async () => {
    expect(await stateExists(tmpDir)).toBe(false);
  });

  it('returns true after writing state', async () => {
    await writeState(tmpDir, baseState);
    expect(await stateExists(tmpDir)).toBe(true);
  });
});

describe('writeState and readState', () => {
  it('round-trips state without loss', async () => {
    await writeState(tmpDir, baseState);
    const read = await readState(tmpDir);
    expect(read.bookIdeaName).toBe(baseState.bookIdeaName);
    expect(read.currentStage).toBe(baseState.currentStage);
    expect(read.finalized).toBe(false);
  });
});

describe('patchState', () => {
  it('merges partial update and updates lastUpdatedBy', async () => {
    await writeState(tmpDir, baseState);
    const updated = await patchState(tmpDir, { currentStage: '2-book-planner' });
    expect(updated.currentStage).toBe('2-book-planner');
    expect(updated.lastUpdatedBy).toBe('book-producer');
    // Unchanged fields preserved
    expect(updated.bookIdeaName).toBe('Test Book');
  });
});

describe('markStageComplete', () => {
  it('adds stage to completedSteps', async () => {
    await writeState(tmpDir, baseState);
    const updated = await markStageComplete(tmpDir, '1-book-init');
    expect(updated.completedSteps).toContain('1-book-init');
  });

  it('does not duplicate stages in completedSteps', async () => {
    await writeState(tmpDir, { ...baseState, completedSteps: ['1-book-init'] });
    const updated = await markStageComplete(tmpDir, '1-book-init');
    const count = updated.completedSteps.filter((s) => s === '1-book-init').length;
    expect(count).toBe(1);
  });

  it('removes stage from incompletedStages', async () => {
    await writeState(tmpDir, { ...baseState, incompletedStages: ['1-book-init'] });
    const updated = await markStageComplete(tmpDir, '1-book-init');
    expect(updated.incompletedStages).not.toContain('1-book-init');
  });
});
