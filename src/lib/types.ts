/**
 * Shared TypeScript types for book-producer CLI.
 */

/** Workflow stage identifiers. */
export type StageId =
  | '1-book-init'
  | '2-book-planner'
  | '3-book-designer'
  | '4-chapter-writer'
  | '5-book-reviewer'
  | '6-publish-assembler';

/** Tool-specific orchestration mode. */
export type OrchestrationMode = 'parallel' | 'sequential';

/** Machine-readable runtime state for a book idea. */
export interface BookIdeaState {
  bookIdeaName: string;
  sanitizedBookIdeaName: string;
  bookIdeaMemoryFolder: string;   // .spec/<slug>/ — spec files only
  bookContentDir: string;          // <slug>/ at repo root — chapters + manuscript
  currentStage: StageId | 'none';
  completedSteps: StageId[];
  incompletedStages: StageId[];
  nextRecommendedStep: string;
  lastUpdatedBy: string;
  lastUpdatedAt: string;
  initialized: boolean;
  finalized: boolean;
  orchestrationMode: OrchestrationMode;
  chapterCount: number;
  manuscriptFile: string | null;
}

/** Chapter frontmatter parsed from a chapter .md file. */
export interface ChapterFrontmatter {
  chapter: number;
  title: string;
  status: 'draft' | 'revised' | 'approved';
  word_count_target: number;
  word_count_actual: number;
  assigned_agent: string;
  reviewer_notes: string;
}

/** A single chapter summary entry in chapter-memory.json. */
export interface ChapterMemoryEntry {
  chapter: number;
  title: string;
  status: 'draft' | 'revised' | 'approved';
  summary: string;
  key_facts: string[];
  open_threads: string[];
  word_count: number;
}

/** Full chapter-memory.json structure. */
export interface ChapterMemory {
  version: number;
  chapters: ChapterMemoryEntry[];
}

/** Result of a book-idea name match lookup. */
export type BookIdeaMatchResult =
  | { kind: 'exact'; slug: string }
  | { kind: 'close'; slug: string; suggestion: string }
  | { kind: 'none'; slug: string };

/** Options shared across commands that support --force. */
export interface ForceOptions {
  force?: boolean;
  yes?: boolean;
}
