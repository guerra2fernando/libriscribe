import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PACKAGE_JSON_PATH = path.join(ROOT_DIR, 'package.json');

/**
 * Parse CLI arguments for registry package preparation.
 */
function parseArgs(argv) {
  const options = {
    registry: 'npm',
    out: path.join(ROOT_DIR, '.release', 'npm'),
    scope: process.env.BOOK_PRODUCER_GITHUB_SCOPE ?? process.env.GITHUB_PACKAGE_SCOPE ?? '',
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--registry' && argv[index + 1]) {
      options.registry = argv[index + 1];
      index += 1;
    } else if (arg === '--out' && argv[index + 1]) {
      options.out = path.resolve(ROOT_DIR, argv[index + 1]);
      index += 1;
    } else if (arg === '--scope' && argv[index + 1]) {
      options.scope = argv[index + 1];
      index += 1;
    }
  }

  return options;
}

/**
 * Normalize a GitHub Packages scope so publish output is always scoped correctly.
 */
function normalizeScope(rawScope) {
  const trimmedScope = rawScope.trim().replace(/^@+/, '').toLowerCase();
  if (!trimmedScope) {
    return '';
  }
  return `@${trimmedScope}`;
}

/**
 * Prepare the registry-specific package.json manifest.
 */
function buildRegistryManifest(packageJson, registry, scope) {
  const manifest = {
    ...packageJson,
    publishConfig: {
      ...(packageJson.publishConfig ?? {}),
    },
  };

  if (registry === 'github') {
    const normalizedScope = normalizeScope(scope);
    if (!normalizedScope) {
      throw new Error(
        'GitHub Packages preparation requires --scope @owner or BOOK_PRODUCER_GITHUB_SCOPE.'
      );
    }
    manifest.name = `${normalizedScope}/${packageJson.name.replace(/^@[^/]+\//, '')}`;
    manifest.publishConfig.registry = 'https://npm.pkg.github.com';
  } else {
    delete manifest.publishConfig.registry;
    if (Object.keys(manifest.publishConfig).length === 0) {
      delete manifest.publishConfig;
    }
  }

  return manifest;
}

/**
 * Copy the publishable package contents into the target directory.
 */
async function copyPublishFiles(rootDir, outDir, packageJson) {
  await fs.remove(outDir);
  await fs.ensureDir(outDir);

  for (const entry of packageJson.files ?? []) {
    await fs.copy(path.join(rootDir, entry), path.join(outDir, entry));
  }

  for (const rootFile of ['package.json']) {
    await fs.copy(path.join(rootDir, rootFile), path.join(outDir, rootFile));
  }
}

/**
 * Main CLI entrypoint.
 */
async function main() {
  const options = parseArgs(process.argv.slice(2));
  const packageJson = await fs.readJSON(PACKAGE_JSON_PATH);

  await copyPublishFiles(ROOT_DIR, options.out, packageJson);

  const manifest = buildRegistryManifest(packageJson, options.registry, options.scope);
  await fs.writeJSON(path.join(options.out, 'package.json'), manifest, { spaces: 2 });

  console.log(
    `[book-producer] Prepared ${options.registry} package at ${path.relative(ROOT_DIR, options.out)} (${manifest.name})`
  );
}

main().catch((error) => {
  console.error(`[book-producer] Failed to prepare registry package: ${error.message}`);
  process.exit(1);
});
