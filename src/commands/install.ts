/**
 * install command — copy framework assets into the target repository.
 *
 * Usage:
 *   book-producer install
 *   book-producer install --force   (overwrite existing managed files)
 *   book-producer install --force --yes  (non-interactive, for CI)
 *
 * This command is passive: it only lays down .book-framework/ files.
 * It does NOT activate any stage or create book-idea memory.
 */
import { Command } from 'commander';
import chalk from 'chalk';
import fs from 'fs-extra';
import path from 'path';
import { installFrameworkAssets } from '../lib/template-engine.js';
import { installToolAdapters } from '../lib/tool-adapters.js';
import { requireForceConfirmation } from '../lib/force-policy.js';

export function installCommand(): Command {
  return new Command('install')
    .description('Install book-producer assets into the current repository')
    .option('--force', 'Overwrite existing managed files (reset to package defaults)')
    .option('--yes', 'Skip confirmation prompt (CI use only)')
    .action(async (opts: { force?: boolean; yes?: boolean }) => {
      const repoRoot = process.cwd();
      const targetDir = path.join(repoRoot, '.book-framework');

      if (opts.force) {
        // Guard: print warning and require confirmation before overwriting
        const confirmed = await requireForceConfirmation({
          action:
            'This will overwrite all managed files under .book-framework/ with package defaults. ' +
            'Any manual edits to framework docs and agent instructions will be lost. ' +
            'Managed tool-entry sections outside .book-framework/ will also be refreshed.',
          targets: [path.join(repoRoot, '.book-framework/')],
          ...(opts.yes !== undefined ? { autoYes: opts.yes } : {}),
        });
        if (!confirmed) {
          console.log(chalk.dim('Aborted.'));
          process.exit(0);
        }
      }

      console.log(chalk.cyan('\n  Installing book-producer assets...\n'));

      const { copied, skipped } = await installFrameworkAssets(repoRoot, opts.force ?? false);
      const adapterResult = await installToolAdapters(repoRoot, opts.force ?? false);

      for (const f of copied) {
        console.log(chalk.green(`  ✓  ${path.relative(repoRoot, f)}`));
      }
      for (const f of skipped) {
        console.log(chalk.dim(`  –  skipped (exists): ${path.relative(repoRoot, f)}`));
      }
      for (const f of adapterResult.created) {
        console.log(chalk.green(`  ✓  ${path.relative(repoRoot, f)}`));
      }
      for (const f of adapterResult.updated) {
        console.log(chalk.cyan(`  ↻  updated: ${path.relative(repoRoot, f)}`));
      }
      for (const f of adapterResult.unchanged) {
        console.log(chalk.dim(`  –  adapter unchanged: ${path.relative(repoRoot, f)}`));
      }

      console.log('');
      console.log(
        chalk.white(
          `  ${copied.length + adapterResult.created.length} file(s) installed, ` +
          `${adapterResult.updated.length} updated, ${skipped.length + adapterResult.unchanged.length} skipped.`
        )
      );
      console.log('');

      const hasExisting = await fs.pathExists(path.join(targetDir, 'AGENTS.md'));
      if (hasExisting) {
        console.log(chalk.dim('  Framework installed. Run  book-producer init  to start a book idea.'));
      }
      console.log('');
    });
}
