/**
 * list command — list all book ideas detected under .spec/.
 */
import { Command } from 'commander';
import chalk from 'chalk';
import { listBookIdeaSlugs } from '../lib/book-idea-manager.js';
import { readState, stateExists } from '../lib/state-manager.js';
import path from 'path';

export function listCommand(): Command {
  return new Command('list')
    .description('List all book ideas in this repository')
    .action(async () => {
      const repoRoot = process.cwd();
      const slugs = await listBookIdeaSlugs(repoRoot);

      if (slugs.length === 0) {
        console.log(chalk.dim('\n  No book ideas found. Run  book-producer init  to create one.\n'));
        return;
      }

      console.log(chalk.cyan(`\n  Book ideas (${slugs.length}):\n`));

      for (const slug of slugs) {
        const folder = path.join(repoRoot, '.spec', slug);
        const hasState = await stateExists(folder);
        if (hasState) {
          const state = await readState(folder);
          const finalized = state.finalized ? chalk.dim(' [finalized]') : '';
          const stage = chalk.dim(`stage: ${state.currentStage}`);
          console.log(`  ${chalk.white(slug)}  ${stage}${finalized}`);
        } else {
          console.log(`  ${chalk.white(slug)}  ${chalk.dim('(no state.json)')}`);
        }
      }
      console.log('');
    });
}