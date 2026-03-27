import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import { installToolAdapters } from '../src/lib/tool-adapters.js';

let tmpDir: string;

beforeEach(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-adapters-'));
});

afterEach(async () => {
  await fs.remove(tmpDir);
});

describe('installToolAdapters', () => {
  it('creates all managed tool entrypoint files', async () => {
    const result = await installToolAdapters(tmpDir);
    expect(result.created.length).toBe(5);

    for (const filePath of [
      'AGENTS.md',
      'CLAUDE.md',
      '.github/copilot-instructions.md',
      '.cursor/rules/book-producer.mdc',
      '.agents/workflows/book-producer.md',
    ]) {
      const content = await fs.readFile(path.join(tmpDir, filePath), 'utf-8');
      expect(content).toContain('book-producer');
      expect(content).toContain('.book-framework/AGENTS.md');
    }
  });

  it('updates the managed section without removing user content', async () => {
    const filePath = path.join(tmpDir, 'AGENTS.md');
    await fs.writeFile(filePath, '# User header\n', 'utf-8');

    await installToolAdapters(tmpDir);

    const content = await fs.readFile(filePath, 'utf-8');
    expect(content).toContain('# User header');
    expect(content).toContain('<!-- book-producer:start -->');
    expect(content).toContain('Use `.book-framework/AGENTS.md` as the canonical workflow contract');
  });
});
