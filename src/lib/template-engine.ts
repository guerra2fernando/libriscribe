/**
 * template-engine — copy and stamp framework asset templates into a book-idea folder.
 * Replaces {{BOOK_IDEA_NAME}} and {{DATE}} placeholders in template files.
 */
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';

/** Resolve the assets directory bundled with this package. */
const ASSETS_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../assets'
);

/** Template directory inside assets. */
const TEMPLATES_DIR = path.join(ASSETS_DIR, 'templates');

/** Framework docs directory inside assets. */
const FRAMEWORK_DIR = path.join(ASSETS_DIR, 'framework');

/** Agents directory inside assets. */
const AGENTS_DIR = path.join(ASSETS_DIR, 'agents');

/** Tool adapter docs inside assets. */
const TOOLING_DIR = path.join(ASSETS_DIR, 'tooling');

/** Installed framework target directory inside target repo. */
const INSTALLED_DIR = '.book-framework';

/** Replace template placeholders in a string. */
function stampTemplate(content: string, vars: Record<string, string>): string {
  return Object.entries(vars).reduce(
    (acc, [key, value]) => acc.replaceAll(`{{${key}}}`, value),
    content
  );
}

/**
 * Stamp and write a single template file into the destination path.
 * If the destination already exists and overwrite is false, skip.
 */
export async function stampFile(
  templatePath: string,
  destPath: string,
  vars: Record<string, string>,
  overwrite = false
): Promise<boolean> {
  if (!overwrite && (await fs.pathExists(destPath))) return false;
  const raw = await fs.readFile(templatePath, 'utf-8');
  const stamped = stampTemplate(raw, vars);
  await fs.ensureDir(path.dirname(destPath));
  await fs.writeFile(destPath, stamped, 'utf-8');
  return true;
}

/**
 * Bootstrap a book-idea memory folder from templates.
 * Stamps 00-current-status, 01-init, and chapter-memory templates.
 * Does not overwrite existing files unless overwrite=true.
 */
export async function bootstrapBookIdeaTemplates(
  bookIdeaFolder: string,
  vars: Record<string, string>,
  overwrite = false
): Promise<string[]> {
  const stamped: string[] = [];
  const templateFiles = [
    '00-current-status.md.template',
    '01-init.md.template',
    'chapter-memory.json.template',
  ];

  for (const tmpl of templateFiles) {
    const src = path.join(TEMPLATES_DIR, tmpl);
    const destName = tmpl.replace('.template', '');
    const dest = tmpl === 'chapter-memory.json.template'
      ? path.join(bookIdeaFolder, 'assets', destName)
      : path.join(bookIdeaFolder, destName);

    const written = await stampFile(src, dest, vars, overwrite);
    if (written) stamped.push(dest);
  }

  return stamped;
}

/**
 * Install framework assets into the target repo under .book-framework/.
 * Copies all framework docs, agent docs, and templates.
 * Skips existing files unless overwrite=true (--force).
 */
export async function installFrameworkAssets(
  repoRoot: string,
  overwrite = false
): Promise<{ copied: string[]; skipped: string[] }> {
  const copied: string[] = [];
  const skipped: string[] = [];
  const targetBase = path.join(repoRoot, INSTALLED_DIR);

  /** Recursively copy a source directory to dest, tracking results. */
  async function copyDir(src: string, dest: string): Promise<void> {
    const entries = await fs.readdir(src, { withFileTypes: true });
    for (const entry of entries) {
      const srcPath = path.join(src, entry.name);
      const destPath = path.join(dest, entry.name);
      if (entry.isDirectory()) {
        await copyDir(srcPath, destPath);
      } else {
        if (!overwrite && (await fs.pathExists(destPath))) {
          skipped.push(destPath);
        } else {
          await fs.ensureDir(path.dirname(destPath));
          await fs.copy(srcPath, destPath, { overwrite: true });
          copied.push(destPath);
        }
      }
    }
  }

  // Copy AGENTS.md + CHAT-WORKFLOW.md
  const agentsMd = path.join(ASSETS_DIR, 'AGENTS.md');
  const agentsDest = path.join(targetBase, 'AGENTS.md');
  if (!overwrite && (await fs.pathExists(agentsDest))) {
    skipped.push(agentsDest);
  } else {
    await fs.ensureDir(targetBase);
    await fs.copy(agentsMd, agentsDest, { overwrite: true });
    copied.push(agentsDest);
  }

  const chatWorkflow = path.join(ASSETS_DIR, 'CHAT-WORKFLOW.md');
  const chatWorkflowDest = path.join(targetBase, 'CHAT-WORKFLOW.md');
  if (!overwrite && (await fs.pathExists(chatWorkflowDest))) {
    skipped.push(chatWorkflowDest);
  } else {
    await fs.ensureDir(targetBase);
    await fs.copy(chatWorkflow, chatWorkflowDest, { overwrite: true });
    copied.push(chatWorkflowDest);
  }

  const readmeMd = path.join(ASSETS_DIR, 'README.md');
  const readmeDest = path.join(targetBase, 'README.md');
  if (!overwrite && (await fs.pathExists(readmeDest))) {
    skipped.push(readmeDest);
  } else {
    await fs.ensureDir(targetBase);
    await fs.copy(readmeMd, readmeDest, { overwrite: true });
    copied.push(readmeDest);
  }

  // Copy framework/, agents/, templates/, tooling/
  await copyDir(FRAMEWORK_DIR, path.join(targetBase, 'framework'));
  await copyDir(AGENTS_DIR, path.join(targetBase, 'agents'));
  await copyDir(TEMPLATES_DIR, path.join(targetBase, 'templates'));
  await copyDir(TOOLING_DIR, path.join(targetBase, 'tooling'));

  return { copied, skipped };
}

/**
 * Return all template file basenames available in the package.
 */
export async function listTemplates(): Promise<string[]> {
  const entries = await fs.readdir(TEMPLATES_DIR);
  return entries.filter((e) => e.endsWith('.template'));
}
