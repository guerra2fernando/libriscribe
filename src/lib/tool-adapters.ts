import fs from 'fs-extra';
import path from 'path';

const SECTION_START = '<!-- book-producer:start -->';
const SECTION_END = '<!-- book-producer:end -->';

interface SectionDefinition {
  filePath: string;
  header?: string;
  prefix?: string;
  body: string;
}

export interface ToolAdapterInstallResult {
  created: string[];
  updated: string[];
  unchanged: string[];
}

/**
 * Build the managed section content for a tool entrypoint file.
 */
function buildManagedSection(header: string | undefined, body: string): string {
  const headerLine = header ? `${header}\n\n` : '';
  return `${SECTION_START}\n${headerLine}${body.trim()}\n${SECTION_END}\n`;
}

/**
 * Replace or append the managed section inside a tool entrypoint file.
 * When force is true, writes the section even if the content is identical.
 */
async function upsertManagedSection(
  filePath: string,
  prefix: string | undefined,
  header: string | undefined,
  body: string,
  force = false
): Promise<'created' | 'updated' | 'unchanged'> {
  const managedSection = buildManagedSection(header, body);
  await fs.ensureDir(path.dirname(filePath));

  if (!(await fs.pathExists(filePath))) {
    const fileContent = prefix ? `${prefix.trim()}\n\n${managedSection}` : managedSection;
    await fs.writeFile(filePath, fileContent, 'utf-8');
    return 'created';
  }

  const existingContent = await fs.readFile(filePath, 'utf-8');
  let nextContent = existingContent;

  if (existingContent.includes(SECTION_START) && existingContent.includes(SECTION_END)) {
    const sectionRegex = new RegExp(
      `${SECTION_START}[\\s\\S]*?${SECTION_END}\\n?`,
      'm'
    );
    nextContent = existingContent.replace(sectionRegex, managedSection);
  } else {
    nextContent = `${existingContent.trimEnd()}\n\n${managedSection}`;
  }

  if (nextContent === existingContent && !force) {
    return 'unchanged';
  }

  await fs.writeFile(filePath, nextContent, 'utf-8');
  return 'updated';
}

/**
 * Shared integration guidance that every tool section can point at.
 */
function buildSharedBody(
  toolName: string,
  toolFile: string
): string {
  let modeLine =
    'Use the matching tool-specific adapter file under `.book-framework/tooling/` and the `book-producer orchestrate` command for the active tool.';

  if (toolName === 'Claude') {
    modeLine = 'Use `book-producer orchestrate ... --tool claude` for parallel chapter or research packets.';
  } else if (toolName !== 'AGENTS') {
    modeLine =
      'Use `book-producer orchestrate ... --tool ' +
      toolName.toLowerCase() +
      '` for serialized work packets; do not parallelize file writes.';
  }

  return [
    `Use \`.book-framework/AGENTS.md\` as the canonical workflow contract for this repository.`,
    `Use \`.book-framework/tooling/${toolFile}\` for ${toolName}-specific adapter details.`,
    'Read `.book-framework/framework/09-orchestration-policy.md` before creating or advancing work packets.',
    'Read `.spec/.branch-mapping.json` when present to resolve the active book on the current branch.',
    'Read `.spec/<book-slug>/state.json` and `00-current-status.md` before continuing work.',
    '`.book-framework/` contains installed framework assets. `.spec/<book-slug>/` contains workflow memory. `<book-slug>/` at repo root contains chapters and the final manuscript.',
    'Initialization creates `00-current-status.md`, `01-init.md`, and `state.json`. Later numbered stage files are created lazily when the user approves the next stage.',
    'Outside initialization, create at most two numbered stage files in one pass: the missing predecessor for recovery and the stage file you are starting now.',
    modeLine,
  ].join('\n');
}

/**
 * Install or refresh managed tool entrypoint sections that point back to the framework.
 * When force is true, all sections are rewritten even if their content is unchanged.
 */
export async function installToolAdapters(repoRoot: string, force = false): Promise<ToolAdapterInstallResult> {
  const definitions: SectionDefinition[] = [
    {
      filePath: path.join(repoRoot, 'AGENTS.md'),
      header: '## book-producer integration',
      body: buildSharedBody('AGENTS', 'shared.md'),
    },
    {
      filePath: path.join(repoRoot, 'CLAUDE.md'),
      header: '## book-producer integration',
      body: buildSharedBody('Claude', 'claude.md'),
    },
    {
      filePath: path.join(repoRoot, '.github', 'copilot-instructions.md'),
      header: '## book-producer integration',
      body: buildSharedBody('Copilot', 'copilot.md'),
    },
    {
      filePath: path.join(repoRoot, '.cursor', 'rules', 'book-producer.mdc'),
      prefix: '---\ndescription: book-producer workflow integration\nglobs:\nalwaysApply: true\n---',
      body: buildSharedBody('Cursor', 'cursor.md'),
    },
    {
      filePath: path.join(repoRoot, '.agents', 'workflows', 'book-producer.md'),
      header: '# book-producer integration',
      body: buildSharedBody('Antigravity', 'antigravity.md'),
    },
  ];

  const result: ToolAdapterInstallResult = {
    created: [],
    updated: [],
    unchanged: [],
  };

  for (const definition of definitions) {
    const outcome = await upsertManagedSection(
      definition.filePath,
      definition.prefix,
      definition.header,
      definition.body,
      force
    );
    if (outcome === 'created') {
      result.created.push(definition.filePath);
    } else if (outcome === 'updated') {
      result.updated.push(definition.filePath);
    } else {
      result.unchanged.push(definition.filePath);
    }
  }

  return result;
}
