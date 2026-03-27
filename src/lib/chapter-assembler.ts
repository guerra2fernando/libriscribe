/**
 * chapter-assembler — collect, sort, and concatenate chapter files
 * into a single final manuscript Markdown file.
 *
 * Used exclusively by the 6-publish-assembler stage.
 *
 * Chapter files live at: <book-slug>/chapters/  (REPO ROOT, not inside .spec/)
 * Final manuscript:       <book-slug>/manuscript-<slug>-final.md
 */
import fs from 'fs-extra';
import path from 'path';
import type { ChapterFrontmatter } from './types.js';

/** Regex to extract YAML frontmatter block from a Markdown file. */
const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n/;

/**
 * Parse a simple key: value YAML frontmatter block.
 * Only handles string and number scalar values — no nested objects.
 */
function parseFrontmatter(raw: string): Partial<ChapterFrontmatter> {
  const result: Record<string, unknown> = {};
  for (const line of raw.split('\n')) {
    const match = /^(\w+):\s*(.+)$/.exec(line.trim());
    if (!match) continue;
    const [, key, value] = match;
    const num = Number(value);
    result[key] = isNaN(num) ? value.replace(/^["']|["']$/g, '') : num;
  }
  return result as Partial<ChapterFrontmatter>;
}

export interface ChapterFile {
  filePath: string;
  frontmatter: Partial<ChapterFrontmatter>;
  rawContent: string;
}

/**
 * Read all chapter .md files from the chapters/ directory.
 * Returns them sorted by chapter number (frontmatter.chapter field).
 */
export async function readChapterFiles(chaptersDir: string): Promise<ChapterFile[]> {
  const entries = await fs.readdir(chaptersDir);
  const mdFiles = entries.filter((e) => e.endsWith('.md'));

  const chapters: ChapterFile[] = [];
  for (const file of mdFiles) {
    const filePath = path.join(chaptersDir, file);
    const content = await fs.readFile(filePath, 'utf-8');
    const fmMatch = FRONTMATTER_RE.exec(content);
    const frontmatter = fmMatch ? parseFrontmatter(fmMatch[1]) : {};
    chapters.push({ filePath, frontmatter, rawContent: content });
  }

  // Sort by chapter number; files without a chapter number go last
  chapters.sort((a, b) => (a.frontmatter.chapter ?? 9999) - (b.frontmatter.chapter ?? 9999));
  return chapters;
}

export interface AssemblyResult {
  manuscriptPath: string;
  includedChapters: number[];
  skippedChapters: number[];
  totalWords: number;
  warnings: string[];
}

/**
 * Validate chapter ordering: detect gaps and duplicate chapter numbers.
 * Returns a list of human-readable warning strings.
 */
export function validateChapterOrder(chapters: ChapterFile[]): string[] {
  const warnings: string[] = [];
  const nums = chapters
    .map((c) => c.frontmatter.chapter)
    .filter((n): n is number => typeof n === 'number' && n !== 9999);

  if (nums.length === 0) {
    warnings.push(
      'No chapter number fields found in frontmatter. ' +
      'Add `chapter: N` and `title: "Chapter N: <name>"` to each file for ordered assembly.'
    );
    return warnings;
  }

  // Detect duplicates
  const seen = new Set<number>();
  for (const n of nums) {
    if (seen.has(n)) {
      warnings.push(`Duplicate chapter number: ${n}. Each chapter must have a unique number.`);
    }
    seen.add(n);
  }

  // Detect gaps (expect 1 … max to be contiguous)
  const sorted = [...nums].sort((a, b) => a - b);
  const start = sorted[0];
  const end = sorted[sorted.length - 1];
  for (let i = start; i <= end; i++) {
    if (!seen.has(i)) {
      warnings.push(`Missing chapter ${i}. Found chapters ${sorted.join(', ')} — gap at ${i}.`);
    }
  }

  // Detect chapters whose title does not follow "Chapter N: ..." convention
  for (const ch of chapters) {
    const { chapter, title } = ch.frontmatter;
    if (typeof chapter === 'number' && title) {
      const expected = `Chapter ${chapter}:`;
      if (!title.startsWith(expected)) {
        warnings.push(
          `Chapter ${chapter} title "${title}" does not follow the recommended format "Chapter ${chapter}: <name>".`
        );
      }
    }
  }

  return warnings;
}

/**
 * Assemble all chapter files into a single final manuscript Markdown file.
 *
 * Reads chapters from `<bookContentDir>/chapters/` (repo root).
 * Writes manuscript to `<bookContentDir>/manuscript-<bookIdeaName>-final.md`.
 * Direct copy/concatenate — no content rewriting.
 *
 * Returns warnings for missing chapter numbers, gaps, or non-standard title formats.
 */
export async function assembleManuscript(
  bookContentDir: string,
  bookIdeaName: string
): Promise<AssemblyResult> {
  const chaptersDir = path.join(bookContentDir, 'chapters');
  const chapters = await readChapterFiles(chaptersDir);
  const warnings = validateChapterOrder(chapters);
  const parts: string[] = [];
  let totalWords = 0;

  for (const ch of chapters) {
    parts.push(ch.rawContent.trimEnd());
    totalWords += (ch.frontmatter.word_count_actual ?? 0);
  }

  const manuscript = parts.join('\n\n---\n\n');
  const manuscriptPath = path.join(
    bookContentDir,
    `manuscript-${bookIdeaName}-final.md`
  );

  await fs.writeFile(manuscriptPath, manuscript + '\n', 'utf-8');

  return {
    manuscriptPath,
    includedChapters: chapters.map((c) => c.frontmatter.chapter ?? -1),
    skippedChapters: [],
    totalWords,
    warnings,
  };
}
