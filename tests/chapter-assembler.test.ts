/**
 * Tests for chapter-assembler: read, filter, sort, and manuscript assembly.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import { readChapterFiles, assembleManuscript, validateChapterOrder } from '../src/lib/chapter-assembler.js';

let tmpDir: string;

function makeChapter(
  num: number,
  title: string,
  status: 'draft' | 'revised' | 'approved',
  body: string
): string {
  // Use the canonical title format: "Chapter N: <name>"
  const canonicalTitle = title.startsWith(`Chapter ${num}:`) ? title : `Chapter ${num}: ${title}`;
  return `---\nchapter: ${num}\ntitle: "${canonicalTitle}"\nstatus: ${status}\nword_count_target: 1000\nword_count_actual: ${body.split(' ').length}\nassigned_agent: chapter-writer\nreviewer_notes: ""\n---\n\n# ${canonicalTitle}\n\n${body}\n`;
}

beforeEach(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-assemble-'));
  // chapters live at <bookContentDir>/chapters/ (repo root model)
  await fs.ensureDir(path.join(tmpDir, 'chapters'));
});

afterEach(async () => {
  await fs.remove(tmpDir);
});

describe('readChapterFiles', () => {
  it('returns empty array for empty chapters dir', async () => {
    const files = await readChapterFiles(path.join(tmpDir, 'chapters'));
    expect(files).toHaveLength(0);
  });

  it('reads and sorts chapters by number', async () => {
    await fs.writeFile(path.join(tmpDir, 'chapters', '02-second.md'), makeChapter(2, 'Second', 'approved', 'Second chapter content.'));
    await fs.writeFile(path.join(tmpDir, 'chapters', '01-first.md'), makeChapter(1, 'First', 'approved', 'First chapter content.'));
    const files = await readChapterFiles(path.join(tmpDir, 'chapters'));
    expect(files[0].frontmatter.chapter).toBe(1);
    expect(files[1].frontmatter.chapter).toBe(2);
  });

  it('parses frontmatter correctly', async () => {
    await fs.writeFile(path.join(tmpDir, 'chapters', '01-test.md'), makeChapter(1, 'Test Chapter', 'draft', 'Some content here.'));
    const files = await readChapterFiles(path.join(tmpDir, 'chapters'));
    expect(files[0].frontmatter.title).toBe('Chapter 1: Test Chapter');
    expect(files[0].frontmatter.status).toBe('draft');
  });
});

describe('validateChapterOrder', () => {
  it('returns no warnings for sequential chapters with correct title format', () => {
    const chapters = [
      { filePath: '01.md', frontmatter: { chapter: 1, title: 'Chapter 1: Opening' }, rawContent: '' },
      { filePath: '02.md', frontmatter: { chapter: 2, title: 'Chapter 2: Rising' }, rawContent: '' },
      { filePath: '03.md', frontmatter: { chapter: 3, title: 'Chapter 3: Climax' }, rawContent: '' },
    ];
    const warnings = validateChapterOrder(chapters);
    expect(warnings).toHaveLength(0);
  });

  it('warns about missing chapter number (gap)', () => {
    const chapters = [
      { filePath: '01.md', frontmatter: { chapter: 1, title: 'Chapter 1: Opening' }, rawContent: '' },
      { filePath: '03.md', frontmatter: { chapter: 3, title: 'Chapter 3: Climax' }, rawContent: '' },
    ];
    const warnings = validateChapterOrder(chapters);
    expect(warnings.some((w) => w.includes('Missing chapter 2'))).toBe(true);
  });

  it('warns about duplicate chapter numbers', () => {
    const chapters = [
      { filePath: '01a.md', frontmatter: { chapter: 1, title: 'Chapter 1: Opening' }, rawContent: '' },
      { filePath: '01b.md', frontmatter: { chapter: 1, title: 'Chapter 1: Duplicate' }, rawContent: '' },
    ];
    const warnings = validateChapterOrder(chapters);
    expect(warnings.some((w) => w.includes('Duplicate chapter number: 1'))).toBe(true);
  });

  it('warns when title does not follow Chapter N: format', () => {
    const chapters = [
      { filePath: '01.md', frontmatter: { chapter: 1, title: 'The Opening Scene' }, rawContent: '' },
    ];
    const warnings = validateChapterOrder(chapters);
    expect(warnings.some((w) => w.includes('does not follow the recommended format'))).toBe(true);
  });

  it('warns when no chapter numbers present', () => {
    const chapters = [
      { filePath: '01.md', frontmatter: { title: 'Untitled' }, rawContent: '' },
    ];
    const warnings = validateChapterOrder(chapters);
    expect(warnings.some((w) => w.includes('No chapter number fields found'))).toBe(true);
  });
});

describe('assembleManuscript', () => {
  it('includes all chapter files in chapter order', async () => {
    await fs.writeFile(path.join(tmpDir, 'chapters', '01-approved.md'), makeChapter(1, 'Approved Chapter', 'approved', 'Approved content.'));
    await fs.writeFile(path.join(tmpDir, 'chapters', '02-draft.md'), makeChapter(2, 'Draft Chapter', 'draft', 'Draft content.'));
    const result = await assembleManuscript(tmpDir, 'my-book');
    expect(result.includedChapters).toContain(1);
    expect(result.includedChapters).toContain(2);
    expect(result.skippedChapters).toEqual([]);
  });

  it('writes manuscript file to book content dir (repo root)', async () => {
    await fs.writeFile(path.join(tmpDir, 'chapters', '01-chapter.md'), makeChapter(1, 'Chapter One', 'approved', 'The story begins here.'));
    const result = await assembleManuscript(tmpDir, 'test-book');
    expect(await fs.pathExists(result.manuscriptPath)).toBe(true);
    expect(result.manuscriptPath).toContain('manuscript-test-book-final.md');
  });

  it('copies chapter content without rewriting', async () => {
    const chapterContent = makeChapter(1, 'Only Chapter', 'approved', 'Clean prose here.');
    await fs.writeFile(path.join(tmpDir, 'chapters', '01-chapter.md'), chapterContent);
    const result = await assembleManuscript(tmpDir, 'test-book');
    const content = await fs.readFile(result.manuscriptPath, 'utf-8');
    expect(content).toContain('word_count_target');
    expect(content).toContain('Clean prose here.');
    expect(content.trim()).toBe(chapterContent.trim());
  });
});
