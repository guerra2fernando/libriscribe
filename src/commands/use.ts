/**
 * use command — switch active book-idea context.
 */
import { Command } from 'commander';
import chalk from 'chalk';
import fs from 'fs-extra';
import path from 'path';
import { listBookIdeaSlugs } from '../lib/book-idea-manager.js';
import { readState, stateExists } from '../lib/state-manager.js';

const ACTIVE_FILE = '.book-framework/.active-book-idea';

export function useCommand(): Command {
  return new Command('use')
    .description('Set the active book idea context')
    .argument('<slug>', 'Book-idea slug (as shown by list)')
    .action(async (slug: string) => {
      const repoRoot = process.cwd();
      const bookIdeaFolder = path.join(repoRoot, '.spec', slug);
      const slugs = await listBookIdeaSlugs(repoRoot);

      if (!slugs.includes(slug)) {
        console.error(chalk.red(`\n  ✗  Book idea "${slug}" not found.\n`));
        console.error(chalk.dim('  Run  book-producer list  to see available book ideas.'));
        process.exit(1);
      }

      const activeFile = path.join(repoRoot, ACTIVE_FILE);
      await fs.ensureDir(path.dirname(activeFile));
      await fs.writeFile(activeFile, slug + '\n', 'utf-8');

      console.log(chalk.green(`\n  ✓  Active book idea set to "${slug}"\n`));
      if (await stateExists(bookIdeaFolder)) {
        const state = await readState(bookIdeaFolder);
        console.log(chalk.dim(`     Current stage: ${state.currentStage}`));
        console.log(chalk.dim(`     Next step: ${state.nextRecommendedStep}`));
      }
      console.log('');
    });
}