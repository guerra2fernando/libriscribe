/**
 * branch-mapper — manages .spec/.branch-mapping.json
 *
 * Tracks which book ideas have been worked on per git branch.
 * Enables multi-book repositories, cross-branch work, and
 * automatic context resolution in chat without user confirmation.
 *
 * AGENT RESOLUTION RULES:
 * - 1 book on current branch → use it automatically
 * - multiple books on current branch → ask unless user mentioned book name
 * - 0 books on current branch → list all books, ask
 * - user mentions book name in message → use it directly, no confirmation
 */
import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import { SPEC_ROOT } from './constants.js';

const MAPPING_FILE = '.branch-mapping.json';

export interface BookBranchEntry {
  displayName: string;
  branches: string[];
  createdAt: string;
}

export interface BranchMapping {
  version: number;
  branches: Record<string, string[]>; // branch → [bookSlug, ...]
  books: Record<string, BookBranchEntry>; // bookSlug → entry
}

function mappingPath(repoRoot: string): string {
  return path.join(repoRoot, SPEC_ROOT, MAPPING_FILE);
}

/** Read the branch mapping file, returning an empty mapping if not present or if the file is corrupt. */
export async function readBranchMapping(repoRoot: string): Promise<BranchMapping> {
  const p = mappingPath(repoRoot);
  if (!(await fs.pathExists(p))) {
    return { version: 1, branches: {}, books: {} };
  }
  let raw: string;
  try {
    raw = await fs.readFile(p, 'utf-8');
  } catch {
    // File exists but cannot be read (permissions). Return empty mapping.
    console.warn(`[book-producer] Warning: cannot read .spec/.branch-mapping.json — returning empty mapping.`);
    return { version: 1, branches: {}, books: {} };
  }
  try {
    return JSON.parse(raw) as BranchMapping;
  } catch {
    console.warn(
      `[book-producer] Warning: .spec/.branch-mapping.json contains invalid JSON.\n` +
      `  Recovery: delete .spec/.branch-mapping.json — it will be recreated on next init.`
    );
    return { version: 1, branches: {}, books: {} };
  }
}

/** Write the branch mapping file. */
export async function writeBranchMapping(
  repoRoot: string,
  mapping: BranchMapping
): Promise<void> {
  const p = mappingPath(repoRoot);
  await fs.ensureDir(path.dirname(p));
  await fs.writeFile(p, JSON.stringify(mapping, null, 2) + '\n', 'utf-8');
}

/**
 * Get the current git branch name, or 'default' if not in a git repo.
 * `git symbolic-ref --short HEAD` succeeds even on unborn branches before the
 * first commit, which keeps branch-aware installs stable in fresh repositories.
 */
export function getCurrentBranch(repoRoot: string): string {
  for (const command of ['git symbolic-ref --short HEAD', 'git rev-parse --abbrev-ref HEAD']) {
    try {
      const branchName = execSync(command, {
        cwd: repoRoot,
        stdio: ['ignore', 'pipe', 'ignore'],
      })
        .toString()
        .trim();
      if (branchName && branchName !== 'HEAD') {
        return branchName;
      }
    } catch {
      // Try the next branch-detection strategy before falling back.
    }
  }
  return 'default';
}

/**
 * Register a book on the current branch.
 * Creates or updates the mapping entry, adding this branch to the book's list.
 */
export async function registerBookOnBranch(
  repoRoot: string,
  bookSlug: string,
  displayName: string
): Promise<void> {
  const branch = getCurrentBranch(repoRoot);
  const mapping = await readBranchMapping(repoRoot);

  // Update branches → books
  if (!mapping.branches[branch]) {
    mapping.branches[branch] = [];
  }
  if (!mapping.branches[branch].includes(bookSlug)) {
    mapping.branches[branch].push(bookSlug);
  }

  // Update books → branches
  if (!mapping.books[bookSlug]) {
    mapping.books[bookSlug] = {
      displayName,
      branches: [],
      createdAt: new Date().toISOString(),
    };
  }
  if (!mapping.books[bookSlug].branches.includes(branch)) {
    mapping.books[bookSlug].branches.push(branch);
  }
  // Update displayName if changed
  mapping.books[bookSlug].displayName = displayName;

  await writeBranchMapping(repoRoot, mapping);
}

/**
 * Get book slugs active on the current branch.
 */
export async function getBooksOnCurrentBranch(repoRoot: string): Promise<string[]> {
  const branch = getCurrentBranch(repoRoot);
  const mapping = await readBranchMapping(repoRoot);
  return mapping.branches[branch] ?? [];
}

/**
 * Get all branches a given book has been worked on.
 */
export async function getBranchesForBook(
  repoRoot: string,
  bookSlug: string
): Promise<string[]> {
  const mapping = await readBranchMapping(repoRoot);
  return mapping.books[bookSlug]?.branches ?? [];
}

/**
 * Resolve which book to use given the current branch context.
 *
 * Returns:
 * - { kind: 'resolved', slug } if exactly one book is on current branch
 * - { kind: 'ambiguous', slugs } if multiple books are on current branch
 * - { kind: 'none' } if no books on current branch (fall back to full .spec/ list)
 */
export async function resolveActiveBook(
  repoRoot: string
): Promise<
  | { kind: 'resolved'; slug: string; displayName: string }
  | { kind: 'ambiguous'; slugs: string[]; displayNames: string[] }
  | { kind: 'none' }
> {
  const books = await getBooksOnCurrentBranch(repoRoot);
  const mapping = await readBranchMapping(repoRoot);

  if (books.length === 1) {
    const slug = books[0];
    return {
      kind: 'resolved',
      slug,
      displayName: mapping.books[slug]?.displayName ?? slug,
    };
  }
  if (books.length > 1) {
    return {
      kind: 'ambiguous',
      slugs: books,
      displayNames: books.map((s) => mapping.books[s]?.displayName ?? s),
    };
  }
  return { kind: 'none' };
}
