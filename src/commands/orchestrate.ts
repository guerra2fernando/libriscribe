import { Command } from 'commander';
import chalk from 'chalk';
import path from 'path';
import fs from 'fs-extra';
import { readState } from '../lib/state-manager.js';
import { resolveActiveBook } from '../lib/branch-mapper.js';
import type { SupportedTool, WorkPlan } from '../lib/work-orchestrator.js';
import {
  buildChapterPlan,
  buildResearchPlan,
  writeWorkPlan,
} from '../lib/work-orchestrator.js';

const SUPPORTED_TOOLS = ['claude', 'copilot', 'cursor', 'antigravity'] as const;

/**
 * Resolve a book slug from the CLI arg or current branch context.
 */
async function resolveSlug(slugArg: string | undefined, repoRoot: string): Promise<string> {
  if (slugArg) {
    return slugArg;
  }

  const resolution = await resolveActiveBook(repoRoot);
  if (resolution.kind === 'resolved') {
    return resolution.slug;
  }

  throw new Error('Unable to resolve an active book. Pass an explicit slug.');
}

/**
 * Validate and normalize the requested tool name.
 */
function parseTool(rawTool: string): SupportedTool {
  if ((SUPPORTED_TOOLS as readonly string[]).includes(rawTool)) {
    return rawTool as SupportedTool;
  }
  throw new Error(`Unsupported tool "${rawTool}". Use one of: ${SUPPORTED_TOOLS.join(', ')}`);
}

/**
 * Render a markdown-style summary for terminal output.
 */
function formatPlan(plan: WorkPlan, planPath: string): string {
  const lines = [
    '',
    `Tool: ${plan.tool}`,
    `Book: ${plan.slug}`,
    `Work kind: ${plan.workKind}`,
    `Execution mode: ${plan.executionMode}`,
    `Saved plan: ${planPath}`,
    '',
    `${plan.summary}`,
    '',
    'Instruction files:',
    ...plan.instructionFiles.map((instructionFile) => `  - ${instructionFile}`),
    '',
    'Packets:',
    ...plan.packets.flatMap((packet) => [
      `  - ${packet.id}: ${packet.title}`,
      `    objective: ${packet.objective}`,
      `    write targets: ${packet.writeTargets.join(', ')}`,
    ]),
    '',
  ];

  return lines.join('\n');
}

/**
 * Register the orchestration helper command for tool-specific work plans.
 */
export function orchestrateCommand(): Command {
  const command = new Command('orchestrate')
    .description('Generate tool-specific chapter or research work packets');

  command
    .command('chapters [slug]')
    .description('Generate chapter-writing packets for a supported AI tool')
    .requiredOption('--chapters <chapters>', 'Comma-separated chapter numbers')
    .requiredOption('--tool <tool>', 'claude, copilot, cursor, or antigravity')
    .option('--json', 'Output machine-readable JSON')
    .action(async (slugArg: string | undefined, opts: { chapters: string; tool: string; json?: boolean }) => {
      try {
        const repoRoot = process.cwd();
        const slug = await resolveSlug(slugArg, repoRoot);
        const tool = parseTool(opts.tool);
        const specFolder = path.join(repoRoot, '.spec', slug);

        if (!(await fs.pathExists(specFolder))) {
          throw new Error(`Book idea not found: ${slug}`);
        }

        const state = await readState(specFolder);
        const chapters = opts.chapters
          .split(',')
          .map((chapterNumber) => Number(chapterNumber.trim()))
          .filter((chapterNumber) => Number.isInteger(chapterNumber) && chapterNumber > 0);

        if (chapters.length === 0) {
          throw new Error('At least one valid chapter number is required.');
        }

        const plan = buildChapterPlan(slug, chapters, tool, state.orchestrationMode);
        const planPath = await writeWorkPlan(repoRoot, plan);

        if (opts.json) {
          console.log(JSON.stringify({ ...plan, planPath }, null, 2));
          return;
        }

        console.log(chalk.cyan(formatPlan(plan, planPath)));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  command
    .command('research [slug]')
    .description('Generate research packets for a supported AI tool')
    .requiredOption('--topics <topics>', 'Comma-separated research topics')
    .requiredOption('--tool <tool>', 'claude, copilot, cursor, or antigravity')
    .option('--json', 'Output machine-readable JSON')
    .action(async (slugArg: string | undefined, opts: { topics: string; tool: string; json?: boolean }) => {
      try {
        const repoRoot = process.cwd();
        const slug = await resolveSlug(slugArg, repoRoot);
        const tool = parseTool(opts.tool);
        const specFolder = path.join(repoRoot, '.spec', slug);

        if (!(await fs.pathExists(specFolder))) {
          throw new Error(`Book idea not found: ${slug}`);
        }

        const state = await readState(specFolder);
        const topics = opts.topics
          .split(',')
          .map((topic) => topic.trim())
          .filter(Boolean);

        if (topics.length === 0) {
          throw new Error('At least one research topic is required.');
        }

        const plan = buildResearchPlan(slug, topics, tool, state.orchestrationMode);
        const planPath = await writeWorkPlan(repoRoot, plan);

        if (opts.json) {
          console.log(JSON.stringify({ ...plan, planPath }, null, 2));
          return;
        }

        console.log(chalk.cyan(formatPlan(plan, planPath)));
      } catch (error) {
        console.error(chalk.red(`Error: ${(error as Error).message}`));
        process.exit(1);
      }
    });

  return command;
}
