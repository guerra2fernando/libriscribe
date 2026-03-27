/**
 * Integration tests — verify that all expected package assets exist on disk.
 *
 * These tests guard against missing template files or asset directories that
 * would cause failures when the package is installed in a user repository.
 *
 * Does NOT require npm pack; verifies source-level presence of all shipped content.
 */
import { describe, it, expect } from 'vitest';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.resolve(__dirname, '..');
const ASSETS = path.join(PACKAGE_ROOT, 'assets');

// ── Template files ───────────────────────────────────────────────────────────

/** All mandatory template files that must exist. Stage 5 (review) is optional but present. */
const REQUIRED_TEMPLATES = [
  '00-current-status.md.template',
  '01-init.md.template',
  '02-plan.md.template',
  '03-design.md.template',
  '04-implementation.md.template',
  '06-finalization.md.template',
  'chapter.md.template',
  'chapter-memory.json.template',
  'state.json.template',
] as const;

/** Recommended optional templates (present but not mandatory for init flow). */
const OPTIONAL_TEMPLATES = ['05-review.md.template'] as const;

// ── Stage agent files ────────────────────────────────────────────────────────

const REQUIRED_STAGE_AGENTS = [
  '1-book-init.md',
  '2-book-planner.md',
  '3-book-designer.md',
  '4-chapter-writer.md',
  '5-book-reviewer.md',
  '6-publish-assembler.md',
] as const;

// ── Framework rule files ─────────────────────────────────────────────────────

const REQUIRED_FRAMEWORK_FILES = [
  '01-core-rules.md',
  '02-state-model.md',
  '03-stage-lifecycle.md',
  '04-command-routing.md',
  '08-skip-force-policy.md',
  '09-orchestration-policy.md',
] as const;

// ── Root asset files ─────────────────────────────────────────────────────────

const REQUIRED_ROOT_ASSETS = ['AGENTS.md', 'CHAT-WORKFLOW.md'] as const;

const REQUIRED_TOOLING_FILES = [
  'shared.md',
  'claude.md',
  'copilot.md',
  'cursor.md',
  'antigravity.md',
] as const;

// ── Package documentation files ──────────────────────────────────────────────

const REQUIRED_PACKAGE_FILES = [
  'README.md',
  'CHANGELOG.md',
  'VERSIONS.md',
  'TROUBLESHOOTING.md',
  'UPGRADING.md',
  'LICENSE',
] as const;

// ── Tests ────────────────────────────────────────────────────────────────────

describe('Package asset completeness', () => {
  for (const tmpl of REQUIRED_TEMPLATES) {
    it(`required template exists: ${tmpl}`, async () => {
      const p = path.join(ASSETS, 'templates', tmpl);
      expect(await fs.pathExists(p), `Missing required template: ${p}`).toBe(true);
    });
  }

  for (const tmpl of OPTIONAL_TEMPLATES) {
    it(`optional template present: ${tmpl}`, async () => {
      const p = path.join(ASSETS, 'templates', tmpl);
      expect(await fs.pathExists(p), `Optional template missing (non-blocking): ${p}`).toBe(true);
    });
  }

  for (const agent of REQUIRED_STAGE_AGENTS) {
    it(`stage agent exists: ${agent}`, async () => {
      const p = path.join(ASSETS, 'agents', agent);
      expect(await fs.pathExists(p), `Missing stage agent: ${p}`).toBe(true);
    });
  }

  for (const fw of REQUIRED_FRAMEWORK_FILES) {
    it(`framework rule file exists: ${fw}`, async () => {
      const p = path.join(ASSETS, 'framework', fw);
      expect(await fs.pathExists(p), `Missing framework file: ${p}`).toBe(true);
    });
  }

  for (const asset of REQUIRED_ROOT_ASSETS) {
    it(`root asset file exists: ${asset}`, async () => {
      const p = path.join(ASSETS, asset);
      expect(await fs.pathExists(p), `Missing root asset: ${p}`).toBe(true);
    });
  }

  for (const toolingFile of REQUIRED_TOOLING_FILES) {
    it(`tool adapter doc exists: ${toolingFile}`, async () => {
      const p = path.join(ASSETS, 'tooling', toolingFile);
      expect(await fs.pathExists(p), `Missing tooling doc: ${p}`).toBe(true);
    });
  }

  for (const doc of REQUIRED_PACKAGE_FILES) {
    it(`package documentation file exists: ${doc}`, async () => {
      const p = path.join(PACKAGE_ROOT, doc);
      expect(await fs.pathExists(p), `Missing package file: ${p}`).toBe(true);
    });
  }
});

describe('Template content sanity checks', () => {
  it('chapter template uses Chapter N: title format', async () => {
    const p = path.join(ASSETS, 'templates', 'chapter.md.template');
    const content = await fs.readFile(p, 'utf-8');
    expect(content).toContain('Chapter {{CHAPTER_NUMBER}}:');
  });

  it('state.json template has required fields', async () => {
    const p = path.join(ASSETS, 'templates', 'state.json.template');
    const content = await fs.readFile(p, 'utf-8');
    expect(content).toContain('currentStage');
    expect(content).toContain('completedSteps');
    expect(content).toContain('initialized');
    expect(content).toContain('bookContentDir');
  });

  it('00-current-status template has required status fields', async () => {
    const p = path.join(ASSETS, 'templates', '00-current-status.md.template');
    const content = await fs.readFile(p, 'utf-8');
    expect(content).toContain('Current book idea');
    expect(content).toContain('Current stage');
  });
});
