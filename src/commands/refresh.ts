/**
 * refresh command — re-apply managed framework templates to installed assets.
 *
 * Usage:
 *   book-producer refresh
 *   book-producer refresh --force       (overwrite even when existing content is newer)
 *   book-producer refresh --force --yes (non-interactive)
 *
 * Without --force, only missing files are written; existing files are skipped.
 * With --force, all managed files are overwritten (user edits to agent docs lost).
 */
import { Command } from 'commander';
import chalk from 'chalk';
import path from 'path';
import { installFrameworkAssets } from '../lib/template-engine.js';
import { installToolAdapters } from '../lib/tool-adapters.js';
import { requireForceConfirmation } from '../lib/force-policy.js';

export function refreshCommand(): Command {
  return new Command('refresh')
    .description('Re-apply managed framework templates to installed assets')
    .option('--force', 'Overwrite existing files even when they already exist')
    .option('--yes', 'Skip confirmation prompt (CI use only)')
    .action(async (opts: { force?: boolean; yes?: boolean }) => {
      const repoRoot = process.cwd();

      if (opts.force) {
        const confirmed = await requireForceConfirmation({
          action:
            'This will overwrite ALL managed files under .book-framework/ including agent instruction docs. ' +
            'Any manual edits will be lost. Managed tool-entry sections outside .book-framework/ will also be refreshed.',
          targets: [path.join(repoRoot, '.book-framework/')],
          ...(opts.yes !== undefined ? { autoYes: opts.yes } : {}),
        });
        if (!confirmed) {
          console.log(chalk.dim('  Aborted.'));
          process.exit(0);
        }
      }

      console.log(chalk.cyan('\n  Refreshing framework assets...\n'));

      const { copied, skipped } = await installFrameworkAssets(repoRoot, opts.force ?? false);
      const adapterResult = await installToolAdapters(repoRoot);

      for (const f of copied) {
        console.log(chalk.green(`  ✓  ${path.relative(repoRoot, f)}`));
      }
      for (const f of skipped) {
        console.log(chalk.dim(`  –  skipped: ${path.relative(repoRoot, f)}`));
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
          `  ${copied.length + adapterResult.created.length} file(s) refreshed, ` +
          `${adapterResult.updated.length} updated, ${skipped.length + adapterResult.unchanged.length} skipped.\n`
        )
      );
    });
}
