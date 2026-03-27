/**
 * book-idea-manager — slug normalization, match lookup, and book-idea CRUD.
 * Controls how book ideas are named, discovered, and created.
 *
 * DIRECTORY MODEL:
 *   .spec/<slug>/   — spec memory (workflow files, stage docs, assets)
 *   <slug>/         — book content (chapters, manuscript) at REPO ROOT
 */
import fs from 'fs-extra';
import path from 'path';
import type { BookIdeaMatchResult, OrchestrationMode, BookIdeaState } from './types.js';
import { writeState } from './state-manager.js';
import { registerBookOnBranch } from './branch-mapper.js';
import { SPEC_ROOT } from './constants.js';

export function normalizeSlug(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '');
}

function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  );
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] =
        a[i - 1] === b[j - 1]
          ? dp[i - 1][j - 1]
          : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }
  return dp[m][n];
}

export async function listBookIdeaSlugs(repoRoot: string): Promise<string[]> {
  const specDir = path.join(repoRoot, SPEC_ROOT);
  if (!(await fs.pathExists(specDir))) return [];
  const entries = await fs.readdir(specDir, { withFileTypes: true });
  return entries.filter((e) => e.isDirectory()).map((e) => e.name);
}

export async function findBookIdeaMatch(
  repoRoot: string,
  slug: string
): Promise<BookIdeaMatchResult> {
  const existing = await listBookIdeaSlugs(repoRoot);
  if (existing.includes(slug)) {
    return { kind: 'exact', slug };
  }
  const closeMatch = existing.find(
    (s) => levenshtein(s, slug) <= 2 || s.includes(slug) || slug.includes(s)
  );
  if (closeMatch) {
    return { kind: 'close', slug, suggestion: closeMatch };
  }
  return { kind: 'none', slug };
}

export async function resolveBookIdeaFolder(
  repoRoot: string,
  slug: string
): Promise<string> {
  const base = path.join(repoRoot, SPEC_ROOT, slug);
  if (!(await fs.pathExists(base))) return base;
  const year = new Date().getFullYear();
  return path.join(repoRoot, SPEC_ROOT, `${slug}-${year}`);
}

export function buildInitialState(
  bookIdeaName: string,
  slug: string,
  bookIdeaFolder: string,
  bookContentDir: string,
  orchestrationMode: OrchestrationMode
): BookIdeaState {
  return {
    bookIdeaName,
    sanitizedBookIdeaName: slug,
    bookIdeaMemoryFolder: bookIdeaFolder,
    bookContentDir,
    currentStage: '1-book-init',
    completedSteps: [],
    incompletedStages: [],
    nextRecommendedStep: '1-book-init - capture book idea, audience, genre, publishing intent, and success criteria',
    lastUpdatedBy: 'book-producer',
    lastUpdatedAt: new Date().toISOString(),
    initialized: true,
    finalized: false,
    orchestrationMode,
    chapterCount: 0,
    manuscriptFile: null,
  };
}

export async function createBookIdea(
  repoRoot: string,
  bookIdeaName: string,
  orchestrationMode: OrchestrationMode
): Promise<{ folder: string; bookContentDir: string; state: BookIdeaState }> {
  const slug = normalizeSlug(bookIdeaName);
  const folder = await resolveBookIdeaFolder(repoRoot, slug);
  // Spec memory lives under .spec/<slug>/
  await fs.ensureDir(folder);
  await fs.ensureDir(path.join(folder, 'assets'));
  // Book content lives at repo root under <slug>/chapters/
  const bookContentDir = path.join(repoRoot, slug);
  await fs.ensureDir(path.join(bookContentDir, 'chapters'));

  const state = buildInitialState(bookIdeaName, slug, folder, bookContentDir, orchestrationMode);
  await writeState(folder, state);
  // Register on current branch
  await registerBookOnBranch(repoRoot, slug, bookIdeaName);
  return { folder, bookContentDir, state };
}