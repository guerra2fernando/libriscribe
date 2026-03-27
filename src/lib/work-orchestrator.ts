import fs from 'fs-extra';
import path from 'path';
import type { OrchestrationMode } from './types.js';

export type SupportedTool = 'claude' | 'copilot' | 'cursor' | 'antigravity';
export type WorkKind = 'chapters' | 'research';
export type ExecutionMode = 'parallel' | 'sequential';

export interface WorkPacket {
  id: string;
  title: string;
  objective: string;
  instructions: string[];
  writeTargets: string[];
  dependsOn: string[];
}

export interface WorkPlan {
  slug: string;
  tool: SupportedTool;
  workKind: WorkKind;
  executionMode: ExecutionMode;
  stateMode: OrchestrationMode;
  summary: string;
  instructionFiles: string[];
  packets: WorkPacket[];
}

/**
 * Return the effective execution mode for a requested tool.
 */
export function resolveExecutionMode(tool: SupportedTool): ExecutionMode {
  return tool === 'claude' ? 'parallel' : 'sequential';
}

/**
 * Create a compact chapter work plan for the requested tool.
 */
export function buildChapterPlan(
  slug: string,
  chapters: number[],
  tool: SupportedTool,
  stateMode: OrchestrationMode
): WorkPlan {
  const executionMode = resolveExecutionMode(tool);
  const chapterTargets = chapters
    .slice()
    .sort((leftChapter, rightChapter) => leftChapter - rightChapter);

  const packets =
    executionMode === 'parallel' && chapterTargets.length > 1
      ? chapterTargets.map((chapterNumber) => ({
          id: `chapter-${chapterNumber}`,
          title: `Draft chapter ${chapterNumber}`,
          objective: `Draft chapter ${chapterNumber} without editing other chapter files.`,
          instructions: [
            'Read the active stage and design docs before writing.',
            'Write only the assigned chapter file plus shared implementation tracking.',
            'Do not overwrite another in-progress chapter draft.',
          ],
          writeTargets: [
            `${slug}/chapters/${String(chapterNumber).padStart(2, '0')}-*.md`,
            `.spec/${slug}/04-implementation.md`,
            `.spec/${slug}/assets/chapter-memory.json`,
          ],
          dependsOn: [],
        }))
      : [
          {
            id: 'chapter-sequence',
            title: `Draft chapter sequence (${chapterTargets.join(', ')})`,
            objective: `Draft the requested chapters one at a time in order.`,
            instructions: [
              'Read the active stage and design docs before writing.',
              'Finish each chapter before moving to the next one.',
              'Update shared implementation tracking after each completed draft.',
            ],
            writeTargets: [
              `${slug}/chapters/*.md`,
              `.spec/${slug}/04-implementation.md`,
              `.spec/${slug}/assets/chapter-memory.json`,
            ],
            dependsOn: [],
          },
        ];

  return {
    slug,
    tool,
    workKind: 'chapters',
    executionMode,
    stateMode,
    summary:
      executionMode === 'parallel'
        ? `Parallel chapter packets for ${chapterTargets.length} independent chapter assignment(s).`
        : `Sequential chapter packet covering ${chapterTargets.length} chapter assignment(s).`,
    instructionFiles: [
      '.book-framework/AGENTS.md',
      `.book-framework/tooling/${tool}.md`,
      '.book-framework/framework/09-orchestration-policy.md',
    ],
    packets,
  };
}

/**
 * Create a compact research work plan for the requested tool.
 */
export function buildResearchPlan(
  slug: string,
  topics: string[],
  tool: SupportedTool,
  stateMode: OrchestrationMode
): WorkPlan {
  const executionMode = resolveExecutionMode(tool);
  const cleanedTopics = topics.map((topic) => topic.trim()).filter(Boolean);

  const packets =
    executionMode === 'parallel' && cleanedTopics.length > 1
      ? cleanedTopics.map((topic, index) => ({
          id: `research-${index + 1}`,
          title: `Research: ${topic}`,
          objective: `Prepare a research note for "${topic}" without editing another topic file.`,
          instructions: [
            'Capture sources, constraints, and open questions relevant to the active book.',
            'Write findings into the assigned research note only.',
            'Do not alter chapter prose while research packets are in progress.',
          ],
          writeTargets: [`.spec/${slug}/assets/research/${slugifyTopic(topic, index + 1)}.md`],
          dependsOn: [],
        }))
      : [
          {
            id: 'research-sequence',
            title: `Research sequence (${cleanedTopics.join('; ')})`,
            objective: 'Work through each research topic in order and consolidate the notes.',
            instructions: [
              'Capture sources, constraints, and open questions relevant to the active book.',
              'Finish one topic before starting the next.',
              'Keep chapter writing serialized while the research packet is active.',
            ],
            writeTargets: [`.spec/${slug}/assets/research/*.md`],
            dependsOn: [],
          },
        ];

  return {
    slug,
    tool,
    workKind: 'research',
    executionMode,
    stateMode,
    summary:
      executionMode === 'parallel'
        ? `Parallel research packets for ${cleanedTopics.length} independent topic(s).`
        : `Sequential research packet covering ${cleanedTopics.length} topic(s).`,
    instructionFiles: [
      '.book-framework/AGENTS.md',
      `.book-framework/tooling/${tool}.md`,
      '.book-framework/framework/09-orchestration-policy.md',
    ],
    packets,
  };
}

/**
 * Persist the latest work plan under the book assets folder for tool handoff.
 */
export async function writeWorkPlan(repoRoot: string, plan: WorkPlan): Promise<string> {
  const planDir = path.join(repoRoot, '.spec', plan.slug, 'assets', 'orchestration');
  const planPath = path.join(planDir, `${plan.workKind}-${plan.tool}.json`);
  await fs.ensureDir(planDir);
  await fs.writeJSON(planPath, plan, { spaces: 2 });
  return planPath;
}

/**
 * Slugify a research topic for note-file generation.
 */
function slugifyTopic(topic: string, index: number): string {
  const slug = topic
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '');
  return slug || `topic-${index}`;
}
