/**
 * state-manager — read and write book-idea state.json files.
 * All state mutations go through this module to keep state consistent.
 */
import fs from 'fs-extra';
import path from 'path';
import type { BookIdeaState, StageId } from './types.js';

/** Filename for the machine-readable state file inside a book-idea folder. */
const STATE_FILE = 'state.json';

/**
 * Read the state.json for a book-idea folder.
 * Throws a descriptive error if the file does not exist or contains invalid JSON.
 */
export async function readState(bookIdeaFolder: string): Promise<BookIdeaState> {
  const stateFile = path.join(bookIdeaFolder, STATE_FILE);
  let raw: string;
  try {
    raw = await fs.readFile(stateFile, 'utf-8');
  } catch {
    throw new Error(
      `Cannot read state file at ${stateFile}.\n` +
      `The book-idea folder may be missing or inaccessible.\n` +
      `If this book was recently created, try running the init command again.`
    );
  }
  try {
    return JSON.parse(raw) as BookIdeaState;
  } catch {
    throw new Error(
      `state.json at ${stateFile} contains invalid JSON.\n` +
      `This can happen if a previous write was interrupted.\n` +
      `Recovery: delete the file and run book-producer init again, or restore from git.`
    );
  }
}

/**
 * Write (overwrite) the state.json for a book-idea folder.
 * Creates the folder if it does not exist.
 */
export async function writeState(bookIdeaFolder: string, state: BookIdeaState): Promise<void> {
  await fs.ensureDir(bookIdeaFolder);
  const stateFile = path.join(bookIdeaFolder, STATE_FILE);
  const tmpFile = `${stateFile}.tmp-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const payload = JSON.stringify(state, null, 2) + '\n';

  const isTransientRenameError = (error: unknown): boolean => {
    const code = (error as { code?: string })?.code;
    return code === 'EPERM' || code === 'EBUSY';
  };

  const delay = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

  try {
    await fs.writeFile(tmpFile, payload, 'utf-8');
    let moved = false;
    for (let attempt = 0; attempt < 5; attempt++) {
      try {
        await fs.move(tmpFile, stateFile, { overwrite: true });
        moved = true;
        break;
      } catch (error) {
        if (!isTransientRenameError(error) || attempt === 4) {
          throw error;
        }
        await delay(10 * (attempt + 1));
      }
    }
    if (!moved) {
      throw new Error(`Unable to move temporary state file into place: ${stateFile}`);
    }
  } finally {
    if (await fs.pathExists(tmpFile)) {
      await fs.remove(tmpFile);
    }
  }
}

/**
 * Patch a subset of fields on an existing state.json.
 * Merges the provided partial state with the existing state and writes.
 */
export async function patchState(
  bookIdeaFolder: string,
  patch: Partial<BookIdeaState>
): Promise<BookIdeaState> {
  const existing = await readState(bookIdeaFolder);
  const updated: BookIdeaState = {
    ...existing,
    ...patch,
    lastUpdatedBy: 'book-producer',
    lastUpdatedAt: new Date().toISOString(),
  };
  await writeState(bookIdeaFolder, updated);
  return updated;
}

/**
 * Mark a stage as complete: add it to completedSteps, remove from incompletedStages.
 */
export async function markStageComplete(
  bookIdeaFolder: string,
  stage: StageId
): Promise<BookIdeaState> {
  const state = await readState(bookIdeaFolder);
  const completedSteps = state.completedSteps.includes(stage)
    ? state.completedSteps
    : [...state.completedSteps, stage];
  const incompletedStages = state.incompletedStages.filter((s) => s !== stage);
  return patchState(bookIdeaFolder, { completedSteps, incompletedStages });
}

/**
 * Return whether a state.json exists for the given book-idea folder.
 */
export async function stateExists(bookIdeaFolder: string): Promise<boolean> {
  return fs.pathExists(path.join(bookIdeaFolder, STATE_FILE));
}
