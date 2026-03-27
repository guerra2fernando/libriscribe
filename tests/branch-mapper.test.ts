import { describe, it, expect, vi, afterEach } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import { getCurrentBranch, readBranchMapping } from '../src/lib/branch-mapper.js';

vi.mock('child_process', () => ({
  execSync: vi.fn(),
}));

import { execSync } from 'child_process';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('getCurrentBranch edge cases', () => {
  it('returns branch with slash', () => {
    vi.mocked(execSync).mockReturnValue(Buffer.from('feature/my-book\n') as never);
    expect(getCurrentBranch(process.cwd())).toBe('feature/my-book');
  });

  it('returns branch with unicode', () => {
    vi.mocked(execSync).mockReturnValue(Buffer.from('feat/áéí-書\n') as never);
    expect(getCurrentBranch(process.cwd())).toBe('feat/áéí-書');
  });

  it('returns branch containing spaces exactly as git reports it', () => {
    vi.mocked(execSync).mockReturnValue(Buffer.from('feature/my branch\n') as never);
    expect(getCurrentBranch(process.cwd())).toBe('feature/my branch');
  });

  it('falls back to rev-parse when symbolic-ref fails', () => {
    vi.mocked(execSync)
      .mockImplementationOnce(() => {
        throw new Error('unborn branch');
      })
      .mockReturnValueOnce(Buffer.from('feature/recovered\n') as never);
    expect(getCurrentBranch(process.cwd())).toBe('feature/recovered');
  });

  it('falls back to default when both git commands fail', () => {
    vi.mocked(execSync).mockImplementation(() => {
      throw new Error('not a git repo');
    });
    expect(getCurrentBranch(process.cwd())).toBe('default');
  });
});

describe('readBranchMapping permission handling', () => {
  it('returns empty mapping when mapping file exists but cannot be read', async () => {
    const tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'book-fw-branch-map-'));
    const mappingPath = path.join(tmpRoot, '.spec', '.branch-mapping.json');
    await fs.ensureDir(path.dirname(mappingPath));
    await fs.writeFile(mappingPath, '{"version":1}', 'utf-8');

    vi.spyOn(fs, 'readFile').mockRejectedValueOnce(Object.assign(new Error('EACCES'), { code: 'EACCES' }));

    const mapping = await readBranchMapping(tmpRoot);
    expect(mapping).toEqual({ version: 1, branches: {}, books: {} });

    await fs.remove(tmpRoot);
  });
});
