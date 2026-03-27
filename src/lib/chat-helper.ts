/**
 * chat-helper.ts — guidance for chat-based workflow execution.
 *
 * This module provides helpers and documentation for running the book-producer
 * entirely from a chat context (Claude, etc.) without CLI commands.
 *
 * CHAT-FIRST WORKFLOW:
 * 1. User says: "init my book"
 * 2. Agent scans .spec/ for existing ideas
 * 3. Agent creates/resumes .spec/<book-idea>/
 * 4. Agent works stage by stage:
 *    - reads current stage file
 *    - works with user to refine content
 *    - writes stage output
 *    - asks for approval to advance
 * 5. Repeat until stage 6 finalization
 *
 * DIRECTORY MODEL:
 * .book-framework/                 ← installed package assets (NEVER EDIT)
 * .spec/
 *   .branch-mapping.json           ← branch↔book registry
 *   <book-slug>/
 *     state.json                    ← machine-readable state (read before each stage)
 *     00-current-status.md          ← human-readable status
 *     01-init.md                    ← stage 1 concept/acceptance
 *     02-plan.md                    ← stage 2 execution plan
 *     03-design.md                  ← stage 3 final book design
 *     04-implementation.md          ← stage 4+ chapter log
 *     05-review.md                  ← stage 5 editorial review
 *     06-finalization.md            ← stage 6 assembly report
 *     assets/
 *       chapter-memory.json         ← rolling chapter summaries
 * <book-slug>/                      ← at REPO ROOT (not inside .spec)
 *   chapters/
 *     01-<slug>.md                  ← chapter files (stage 4+)
 *   manuscript-<slug>-final.md      ← final assembled output
 *
 * AGENT RESPONSIBILITIES:
 * - At start: resolve book from branch mapping or ask user
 * - Each stage: read stage file + previous outputs + user input
 * - Each stage: work interactively, then write stage file
 * - Get approval: explicit user confirmation before advancing
 * - On stage 4: write chapter files to <book-slug>/chapters/ at repo root
 * - On stage 6: concatenate all approved chapters, write manuscript, await cleanup confirmation
 * - bookIdeaMemoryFolder = .spec/<slug>/   (spec stage files + assets)
 * - bookContentDir       = <slug>/         (chapters + manuscript at repo root)
 *
 * NO CLI COMMANDS NEEDED in chat workflow.
 */

import fs from 'fs-extra';
import path from 'path';
import type { BookIdeaState, ChapterMemory } from './types.js';

export async function readBookIdeaState(
  bookIdeaMemoryFolder: string
): Promise<BookIdeaState> {
  const statePath = path.join(bookIdeaMemoryFolder, 'state.json');
  if (!(await fs.pathExists(statePath))) {
    throw new Error(`state.json not found at ${statePath}`);
  }
  const raw = await fs.readFile(statePath, 'utf-8');
  return JSON.parse(raw) as BookIdeaState;
}

export async function writeBookIdeaState(
  bookIdeaMemoryFolder: string,
  state: BookIdeaState
): Promise<void> {
  const statePath = path.join(bookIdeaMemoryFolder, 'state.json');
  await fs.writeJSON(statePath, state, { spaces: 2 });
}

export async function readStageFile(
  bookIdeaMemoryFolder: string,
  stageNumber: number
): Promise<string> {
  const filename = `0${stageNumber}-`;
  const files = await fs.readdir(bookIdeaMemoryFolder);
  const stageFile = files.find(
    (f) => f.startsWith(filename) && f.endsWith('.md')
  );
  if (!stageFile) {
    throw new Error(`Stage ${stageNumber} file not found in ${bookIdeaMemoryFolder}`);
  }
  const filePath = path.join(bookIdeaMemoryFolder, stageFile);
  return fs.readFile(filePath, 'utf-8');
}

export async function writeStageFile(
  bookIdeaMemoryFolder: string,
  stageNumber: number,
  content: string
): Promise<void> {
  const filename = `0${stageNumber}-`;
  const files = await fs.readdir(bookIdeaMemoryFolder);
  const stageFile = files.find(
    (f) => f.startsWith(filename) && f.endsWith('.md')
  );
  if (!stageFile) {
    throw new Error(`Stage ${stageNumber} file not found in ${bookIdeaMemoryFolder}`);
  }
  const filePath = path.join(bookIdeaMemoryFolder, stageFile);
  await fs.writeFile(filePath, content, 'utf-8');
}

/** Returns the chapters directory — lives at repo root under <book-slug>/chapters/ */
export function getChaptersDirectory(bookContentDir: string): string {
  return path.join(bookContentDir, 'chapters');
}

/** List all chapter .md files from the book content dir (repo root). */
export async function listChapterFiles(
  bookContentDir: string
): Promise<string[]> {
  const chaptersDir = getChaptersDirectory(bookContentDir);
  if (!(await fs.pathExists(chaptersDir))) {
    return [];
  }
  const files = await fs.readdir(chaptersDir);
  return files.filter((f) => f.endsWith('.md')).sort();
}

export async function readChapterFile(
  bookContentDir: string,
  filename: string
): Promise<string> {
  const chaptersDir = getChaptersDirectory(bookContentDir);
  const filePath = path.join(chaptersDir, filename);
  if (!(await fs.pathExists(filePath))) {
    throw new Error(`Chapter file not found: ${filePath}`);
  }
  return fs.readFile(filePath, 'utf-8');
}

export async function writeChapterFile(
  bookContentDir: string,
  filename: string,
  content: string
): Promise<void> {
  const chaptersDir = getChaptersDirectory(bookContentDir);
  await fs.ensureDir(chaptersDir);
  const filePath = path.join(chaptersDir, filename);
  await fs.writeFile(filePath, content, 'utf-8');
}

export async function getChapterMemory(
  bookIdeaMemoryFolder: string
): Promise<ChapterMemory> {
  const memoryPath = path.join(bookIdeaMemoryFolder, 'assets', 'chapter-memory.json');
  if (!(await fs.pathExists(memoryPath))) {
    return { version: 1, chapters: [] };
  }
  const raw = await fs.readFile(memoryPath, 'utf-8');
  return JSON.parse(raw) as ChapterMemory;
}

export async function updateChapterMemory(
  bookIdeaMemoryFolder: string,
  memory: ChapterMemory
): Promise<void> {
  const assetsDir = path.join(bookIdeaMemoryFolder, 'assets');
  await fs.ensureDir(assetsDir);
  const memoryPath = path.join(assetsDir, 'chapter-memory.json');
  await fs.writeJSON(memoryPath, memory, { spaces: 2 });
}

/** Write the final manuscript at <bookContentDir>/manuscript-<slug>-final.md (repo root). */
export async function createManuscriptFile(
  bookContentDir: string,
  content: string,
  bookIdeaName: string
): Promise<string> {
  await fs.ensureDir(bookContentDir);
  const manuscriptPath = path.join(
    bookContentDir,
    `manuscript-${bookIdeaName}-final.md`
  );
  await fs.writeFile(manuscriptPath, content, 'utf-8');
  return manuscriptPath;
}
