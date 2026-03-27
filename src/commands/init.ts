/**
 * init command — create or resume a named book idea.
 *
 * OPTIONAL: This command is provided as a CLI convenience. 
 * In chat-first workflow, the agent creates .spec/<book-idea>/ directly without using this command.
 *
 * Usage (CLI):
 *   book-producer init "My Book Title"
 *   book-producer init "My Book Title" --mode sequential
 *   book-producer init "My Book Title" --force
 *   book-producer init "My Book Title" --force --yes
 */
import { Command } from 'commander';
import chalk from 'chalk';
import inquirer from 'inquirer';
import fs from 'fs-extra';
import path from 'path';
import {
  normalizeSlug,
  findBookIdeaMatch,
  createBookIdea,
} from '../lib/book-idea-manager.js';
import { bootstrapBookIdeaTemplates } from '../lib/template-engine.js';
import { detectOrchestrationMode, describeMode } from '../lib/orchestration.js';
import { requireForceConfirmation } from '../lib/force-policy.js';
import type { OrchestrationMode } from '../lib/types.js';

export function initCommand(): Command {
  return new Command('init')
    .description('Create or resume a named book idea')
    .argument('[name]', 'Book idea name or title')
    .option('--mode <mode>', 'Orchestration mode: parallel or sequential')
    .option('--force', 'Reset bootstrap files for the selected book idea')
    .option('--yes', 'Skip confirmation prompts (CI use only)')
    .action(async (nameArg: string | undefined, opts: { mode?: string; force?: boolean; yes?: boolean }): Promise<void> => {
      const repoRoot = process.cwd();
      let rawName = nameArg;
      if (!rawName) {
        const answer = await inquirer.prompt<{ name: string }>([
          {
            type: 'input',
            name: 'name',
            message: 'What is the name or title of your book idea?',
            validate: (v: string): true | string => v.trim().length > 0 || 'Name cannot be empty.',
          },
        ]);
        rawName = answer.name;
      }

      const slug = normalizeSlug(rawName);
      if (!slug) {
        console.error(chalk.red('  ✗  Could not derive a valid slug from the provided name.'));
        process.exit(1);
      }

      const hasClaudeDir = await fs.pathExists(path.join(repoRoot, '.claude'));
      const detectedMode = detectOrchestrationMode(process.env, hasClaudeDir);
      let orchMode: OrchestrationMode = detectedMode;
      if (opts.mode === 'parallel' || opts.mode === 'sequential') {
        orchMode = opts.mode as OrchestrationMode;
      }

      const match = await findBookIdeaMatch(repoRoot, slug);

      if (match.kind === 'exact') {
        const { choice } = await inquirer.prompt<{ choice: string }>([
          {
            type: 'list',
            name: 'choice',
            message: `Book idea "${slug}" already exists. What would you like to do?`,
            choices: [
              { name: 'Continue existing book idea', value: 'continue' },
              { name: 'Create a new book idea (new name required)', value: 'new' },
            ],
          },
        ]);

        if (choice === 'continue') {
          const folder = path.join(repoRoot, '.spec', slug);
          if (opts.force) {
            const confirmed = await requireForceConfirmation({
              action: `This will reset the bootstrap files (00-current-status.md, 01-init.md) for book idea "${slug}". Chapter files will NOT be deleted.`,
              targets: [path.join(folder, '00-current-status.md'), path.join(folder, '01-init.md')],
              ...(opts.yes !== undefined ? { autoYes: opts.yes } : {}),
            });
            if (!confirmed) {
              console.log(chalk.dim('  Aborted.'));
              process.exit(0);
            }
          }
          const vars = { BOOK_IDEA_NAME: rawName, BOOK_IDEA_SLUG: slug, DATE: new Date().toISOString().split('T')[0] };
          await bootstrapBookIdeaTemplates(folder, vars, opts.force ?? false);
          console.log(chalk.green(`\n  ✓  Book idea "${slug}" resumed at ${folder}\n`));
          console.log(chalk.dim(`  Orchestration mode: ${describeMode(orchMode)}`));
          console.log(chalk.dim('  Run stage 1-book-init to begin or continue.\n'));
          return;
        }

        const { newName } = await inquirer.prompt<{ newName: string }>([
          {
            type: 'input',
            name: 'newName',
            message: 'Enter a different name for the new book idea:',
            validate: (v: string): true | string => {
              const s = normalizeSlug(v);
              return s.length > 0 && s !== slug ? true : 'Please provide a different name.';
            },
          },
        ]);
        rawName = newName;
      } else if (match.kind === 'close') {
        console.log(chalk.yellow(`\n  Similar book idea found: "${match.suggestion}"`));
        const { choice } = await inquirer.prompt<{ choice: string }>([
          {
            type: 'list',
            name: 'choice',
            message: 'Would you like to continue that book idea or create a new one?',
            choices: [
              { name: `Continue "${match.suggestion}"`, value: 'existing' },
              { name: `Create new book idea "${slug}"`, value: 'new' },
            ],
          },
        ]);

        if (choice === 'existing') {
          const folder = path.join(repoRoot, '.spec', match.suggestion);
          const vars = { BOOK_IDEA_NAME: rawName, BOOK_IDEA_SLUG: match.suggestion, DATE: new Date().toISOString().split('T')[0] };
          await bootstrapBookIdeaTemplates(folder, vars, false);
          console.log(chalk.green(`\n  ✓  Book idea "${match.suggestion}" resumed at ${folder}\n`));
          return;
        }
      }

      const { folder, bookContentDir, state } = await createBookIdea(repoRoot, rawName, orchMode);
      const vars = {
        BOOK_IDEA_NAME: rawName,
        BOOK_IDEA_SLUG: state.sanitizedBookIdeaName,
        DATE: new Date().toISOString().split('T')[0],
      };
      await bootstrapBookIdeaTemplates(folder, vars, true);

      console.log('');
      console.log(chalk.green(`  ✓  Book idea "${state.sanitizedBookIdeaName}" created`));
      console.log(chalk.dim(`     Spec   : ${folder}`));
      console.log(chalk.dim(`     Content: ${bookContentDir}`));
      console.log(chalk.dim(`     Orchestration mode: ${describeMode(orchMode)}`));
      console.log('');
      console.log(chalk.white('  Next step: run stage  1-book-init  to capture your book idea.'));
      console.log('');
    });
}