import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import { installFrameworkAssets } from '../src/lib/template-engine.js';

let tmpDir: string;

beforeEach(async () => {
  tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-install-'));
});

afterEach(async () => {
  await fs.remove(tmpDir);
});

describe('installFrameworkAssets', () => {
  it('installs framework assets, chat workflow guide, and tooling docs', async () => {
    const result = await installFrameworkAssets(tmpDir, false);
    expect(result.copied.length).toBeGreaterThan(0);
    expect(await fs.pathExists(path.join(tmpDir, '.book-framework', 'AGENTS.md'))).toBe(true);
    expect(await fs.pathExists(path.join(tmpDir, '.book-framework', 'CHAT-WORKFLOW.md'))).toBe(true);
    expect(await fs.pathExists(path.join(tmpDir, '.book-framework', 'tooling', 'claude.md'))).toBe(true);
    expect(await fs.pathExists(path.join(tmpDir, '.book-framework', 'tooling', 'shared.md'))).toBe(true);
  });
});
