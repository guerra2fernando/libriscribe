import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import { readState, writeState, patchState } from '../src/lib/state-manager.js';
import type { BookIdeaState } from '../src/lib/types.js';

let tmpDir: string;

const baseState: BookIdeaState = {
  bookIdeaName: 'Robustness Book',
  sanitizedBookIdeaName: 'robustness-book',
  bookIdeaMemoryFolder: '.spec/robustness-book',
  bookContentDir: 'robustness-book',
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
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-robustness-'));
});

afterEach(async () => {
  await fs.remove(tmpDir);
});

describe('readState error contract', () => {
  it('throws descriptive recovery message for invalid JSON', async () => {
    const stateFile = path.join(tmpDir, 'state.json');
    await fs.writeFile(stateFile, '{ invalid-json', 'utf-8');

    await expect(readState(tmpDir)).rejects.toThrow(/invalid JSON/i);
    await expect(readState(tmpDir)).rejects.toThrow(/Recovery:/i);
    await expect(readState(tmpDir)).rejects.toThrow(/state\.json/i);
  });

  it('throws descriptive error when state file is missing', async () => {
    await expect(readState(tmpDir)).rejects.toThrow(/Cannot read state file/i);
    await expect(readState(tmpDir)).rejects.toThrow(/init command again/i);
  });
});

describe('concurrent state writes', () => {
  it('keeps state.json valid under concurrent patchState writes', async () => {
    await writeState(tmpDir, baseState);

    const concurrentWrites = Array.from({ length: 20 }, (_, index) =>
      patchState(tmpDir, {
        chapterCount: index,
        nextRecommendedStep: `step-${index}`,
      })
    );

    await Promise.all(concurrentWrites);

    const finalState = await readState(tmpDir);
    expect(typeof finalState.chapterCount).toBe('number');
    expect(finalState.chapterCount).toBeGreaterThanOrEqual(0);
    expect(finalState.chapterCount).toBeLessThan(20);
    expect(finalState.nextRecommendedStep).toMatch(/^step-\d+$/);
  });
});

describe('permission-denied write path', () => {
  it('surfaces EACCES when writeState cannot write file', async () => {
    const originalWriteFile = fs.writeFile;
    const eacces = Object.assign(new Error('EACCES: permission denied'), { code: 'EACCES' });

    fs.writeFile = ((...args: Parameters<typeof fs.writeFile>) => {
      const targetPath = String(args[0]);
      if (targetPath.includes('.tmp-')) {
        return Promise.reject(eacces);
      }
      return originalWriteFile(...args);
    }) as typeof fs.writeFile;

    try {
      await expect(writeState(tmpDir, baseState)).rejects.toThrow(/EACCES|permission denied/i);
    } finally {
      fs.writeFile = originalWriteFile;
    }
  });
});
