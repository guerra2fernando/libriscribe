/**
 * doctor command — validate installed framework assets against the package version.
 *
 * Checks:
 *   - .book-framework/ exists
 *   - Required subdirectories exist (framework/, agents/, templates/, tooling/)
 *   - AGENTS.md and CHAT-WORKFLOW.md are present
 *   - Tool adapter entrypoint files exist
 *   - At least one book idea exists under .spec/ (informational, not an error)
 *
 * Usage:
 *   book-producer doctor
 */
import { Command } from 'commander';
import chalk from 'chalk';
import fs from 'fs-extra';
import path from 'path';
import { listBookIdeaSlugs } from '../lib/book-idea-manager.js';

interface CheckResult {
  label: string;
  ok: boolean;
  note?: string;
}

export function doctorCommand(): Command {
  return new Command('doctor')
    .description('Check installed framework assets and book-idea health')
    .action(async () => {
      const repoRoot = process.cwd();
      const bookFrameworkDir = path.join(repoRoot, '.book-framework');
      const results: CheckResult[] = [];

      // Check .book-framework/
      results.push({
        label: '.book-framework/ exists',
        ok: await fs.pathExists(bookFrameworkDir),
        note: 'Run  book-producer install  to create it.',
      });

      // Check subdirectories
      for (const sub of ['framework', 'agents', 'templates', 'tooling']) {
        results.push({
          label: `.book-framework/${sub}/`,
          ok: await fs.pathExists(path.join(bookFrameworkDir, sub)),
          note: `Run  book-producer install --force  to restore.`,
        });
      }

      // Check AGENTS.md
      results.push({
        label: '.book-framework/AGENTS.md',
        ok: await fs.pathExists(path.join(bookFrameworkDir, 'AGENTS.md')),
        note: 'Run  book-producer install --force  to restore.',
      });
      results.push({
        label: '.book-framework/CHAT-WORKFLOW.md',
        ok: await fs.pathExists(path.join(bookFrameworkDir, 'CHAT-WORKFLOW.md')),
        note: 'Run  book-producer install --force  to restore.',
      });

      // Check tool adapter files
      for (const adapterFile of [
        'AGENTS.md',
        'CLAUDE.md',
        '.github/copilot-instructions.md',
        '.cursor/rules/book-producer.mdc',
        '.agents/workflows/book-producer.md',
      ]) {
        results.push({
          label: adapterFile,
          ok: await fs.pathExists(path.join(repoRoot, adapterFile)),
          note: 'Run  book-producer install --force  to refresh managed tool adapters.',
        });
      }

      // Check book ideas (informational)
      const slugs = await listBookIdeaSlugs(repoRoot);
      results.push({
        label: 'At least one book idea exists',
        ok: slugs.length > 0,
        note: slugs.length === 0
          ? 'Run  book-producer init  to create one.'
          : `Found: ${slugs.join(', ')}`,
      });

      // Print results
      console.log(chalk.cyan('\n  book-producer doctor\n'));
      let hasError = false;
      for (const r of results) {
        if (r.ok) {
          console.log(`  ${chalk.green('✓')}  ${r.label}${r.note ? chalk.dim('  ' + r.note) : ''}`);
        } else {
          hasError = true;
          console.log(`  ${chalk.red('✗')}  ${r.label}  ${chalk.dim(r.note ?? '')}`);
        }
      }

      console.log('');
      if (hasError) {
        console.log(chalk.yellow('  Some checks failed. See notes above.\n'));
        process.exit(1);
      } else {
        console.log(chalk.green('  All checks passed.\n'));
      }
    });
}
