/**
 * status command — show current stage, chapter progress, and branch info for a book idea.
 *
 * Usage:
 *   book-producer status                 # auto-resolve from current branch
 *   book-producer status my-book-slug    # explicit book
 *
 * In chat-first workflow, the agent reads .spec/<slug>/state.json and
 * .spec/.branch-mapping.json directly. This command is the CLI equivalent.
 */
import { Command } from 'commander';
import chalk from 'chalk';
import path from 'path';
import fs from 'fs-extra';
import { readState } from '../lib/state-manager.js';
import {
  resolveActiveBook,
  readBranchMapping,
  getCurrentBranch,
  getBranchesForBook,
} from '../lib/branch-mapper.js';
import { listBookIdeaSlugs } from '../lib/book-idea-manager.js';
import { SPEC_ROOT } from '../lib/constants.js';

const STAGE_LABELS: Record<string, string> = {
  '1-book-init': '1 - Concept & Init',
  '2-book-planner': '2 - Planning',
  '3-book-designer': '3 - Book Design',
  '4-chapter-writer': '4 - Chapter Writing',
  '5-book-reviewer': '5 - Editorial Review',
  '6-publish-assembler': '6 - Finalization',
  'none': 'Complete',
};

export function statusCommand(): Command {
  return new Command('status')
    .description('Show current stage, chapter progress, and branch info for a book idea')
    .argument('[slug]', 'Book idea slug (auto-resolved from current branch if omitted)')
    .option('--json', 'Output machine-readable JSON')
    .action(async (slugArg: string | undefined, opts: { json?: boolean }) => {
      const outputJson = Boolean(opts.json);
      const repoRoot = process.cwd();
      let slug = slugArg;

      // Auto-resolve if not specified
      if (!slug) {
        const resolution = await resolveActiveBook(repoRoot);
        if (resolution.kind === 'resolved') {
          slug = resolution.slug;
        } else if (resolution.kind === 'ambiguous') {
          if (outputJson) {
            console.log(JSON.stringify({
              kind: 'ambiguous',
              currentBranch: getCurrentBranch(repoRoot),
              slugs: resolution.slugs,
              displayNames: resolution.displayNames,
              hint: 'Run: book-producer status <slug>',
            }, null, 2));
          } else {
            console.log(chalk.yellow('\nMultiple book ideas found on current branch:'));
            resolution.slugs.forEach((s, i) => {
              console.log(`  ${i + 1}. ${resolution.displayNames[i]} (${s})`);
            });
            console.log(chalk.dim('\nRun: book-producer status <slug>'));
          }
          process.exit(0);
        } else {
          // No books on current branch — list all
          const allSlugs = await listBookIdeaSlugs(repoRoot);
          if (allSlugs.length === 0) {
            if (outputJson) {
              console.log(JSON.stringify({
                kind: 'none',
                currentBranch: getCurrentBranch(repoRoot),
                slugs: [],
                hint: 'Run: book-producer init "Your Book Title"',
              }, null, 2));
            } else {
              console.log(chalk.yellow('No book ideas found. Run: book-producer init "Your Book Title"'));
            }
            process.exit(0);
          }
          if (outputJson) {
            console.log(JSON.stringify({
              kind: 'none-on-branch',
              currentBranch: getCurrentBranch(repoRoot),
              slugs: allSlugs,
              hint: 'Run: book-producer status <slug>',
            }, null, 2));
          } else {
            console.log(chalk.yellow(`\nNo book ideas found on branch "${getCurrentBranch(repoRoot)}".`));
            console.log('All available book ideas:');
            allSlugs.forEach((s) => console.log(`  - ${s}`));
            console.log(chalk.dim('\nRun: book-producer status <slug>'));
          }
          process.exit(0);
        }
      }

      const specFolder = path.join(repoRoot, SPEC_ROOT, slug);
      if (!(await fs.pathExists(specFolder))) {
        if (outputJson) {
          console.log(JSON.stringify({
            kind: 'not-found',
            slug,
            expectedSpecFolder: specFolder,
          }, null, 2));
        } else {
          console.error(chalk.red(`\nBook idea not found: ${slug}`));
          console.error(chalk.dim(`Expected spec folder: ${specFolder}`));
        }
        process.exit(1);
      }

      // Read state
      const state = await readState(specFolder);

      // Count chapters
      const chaptersDir = path.join(repoRoot, slug, 'chapters');
      let totalChapters = 0;
      let approvedChapters = 0;
      let draftChapters = 0;
      if (await fs.pathExists(chaptersDir)) {
        const files = (await fs.readdir(chaptersDir)).filter((f) => f.endsWith('.md'));
        totalChapters = files.length;
        for (const f of files) {
          const content = await fs.readFile(path.join(chaptersDir, f), 'utf-8');
          if (/^status:\s*approved/m.test(content)) approvedChapters++;
          else if (/^status:\s*draft/m.test(content)) draftChapters++;
        }
      }

      // Branch info
      const activeBranches = await getBranchesForBook(repoRoot, slug);
      const mapping = await readBranchMapping(repoRoot);
      const displayName = mapping.books[slug]?.displayName ?? slug;
      const currentBranch = getCurrentBranch(repoRoot);

      // Manuscript
      const manuscriptPath = path.join(repoRoot, slug, `manuscript-${slug}-final.md`);
      const hasManuscript = await fs.pathExists(manuscriptPath);

      const payload = {
        kind: 'resolved',
        displayName,
        slug,
        stage: {
          current: state.currentStage,
          currentLabel: STAGE_LABELS[state.currentStage] ?? state.currentStage,
          completed: state.completedSteps,
          completedLabels: state.completedSteps.map((s) => STAGE_LABELS[s] ?? s),
          next: state.nextRecommendedStep,
        },
        chapters: {
          total: totalChapters,
          approved: approvedChapters,
          draft: draftChapters,
          progressPercent: totalChapters > 0 ? Math.round((approvedChapters / totalChapters) * 100) : 0,
        },
        branches: {
          current: currentBranch,
          all: activeBranches,
        },
        files: {
          specFolder: `.spec/${slug}/`,
          bookContent: `${slug}/chapters/`,
          manuscript: hasManuscript ? `${slug}/manuscript-${slug}-final.md` : null,
        },
        updatedAt: state.lastUpdatedAt,
      };

      if (outputJson) {
        console.log(JSON.stringify(payload, null, 2));
        return;
      }

      // Output
      console.log('');
      console.log(chalk.bold(`Book: ${displayName}`));
      console.log(chalk.dim(`    slug: ${slug}`));
      console.log('');
      console.log(chalk.bold('Stage'));
      console.log(`  Current:   ${chalk.cyan(STAGE_LABELS[state.currentStage] ?? state.currentStage)}`);
      if (state.completedSteps.length > 0) {
        console.log(`  Completed: ${state.completedSteps.map((s) => STAGE_LABELS[s] ?? s).join(' -> ')}`);
      }
      console.log(`  Next:      ${chalk.green(state.nextRecommendedStep)}`);
      console.log('');
      if (totalChapters > 0) {
        const pct = totalChapters > 0 ? Math.round((approvedChapters / totalChapters) * 100) : 0;
        console.log(chalk.bold('Chapters'));
        console.log(`  Total:    ${totalChapters}`);
        console.log(`  Approved: ${chalk.green(String(approvedChapters))}  Draft: ${chalk.yellow(String(draftChapters))}`);
        console.log(`  Progress: ${pct}%`);
        console.log('');
      }
      console.log(chalk.bold('Branches'));
      console.log(`  Current:  ${chalk.cyan(currentBranch)}`);
      if (activeBranches.length > 0) {
        console.log(`  All:      ${activeBranches.join(', ')}`);
      }
      console.log('');
      console.log(chalk.bold('Files'));
      console.log(`  Spec folder:  .spec/${slug}/`);
      console.log(`  Book content: ${slug}/chapters/`);
      if (hasManuscript) {
        console.log(`  Manuscript:   ${chalk.green(`${slug}/manuscript-${slug}-final.md`)}`);
      }
      console.log(`  Updated:      ${state.lastUpdatedAt}`);
      console.log('');
    });
}
