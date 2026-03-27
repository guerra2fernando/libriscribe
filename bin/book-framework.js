#!/usr/bin/env node
/**
 * book-framework CLI entry point.
 * Delegates to the compiled TypeScript output in ../dist/cli.js.
 */
import('../dist/cli.js').catch((err) => {
  console.error('[book-framework] Failed to load CLI:', err);
  process.exit(1);
});
