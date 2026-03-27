/**
 * orchestration - detect the active tool environment and resolve the
 * appropriate default orchestration mode (parallel or sequential).
 *
 * Detection is performed once at init time and stored in state.json.
 * The user may override via `--mode` flag on init.
 */
import type { OrchestrationMode } from './types.js';

/**
 * Detect orchestration mode from environment signals.
 *
 * Claude indicators (-> parallel):
 *   - ANTHROPIC_API_KEY is set
 *   - CLAUDE_* env vars present
 *   - .claude/ directory exists in CWD (checked externally and passed in)
 *
 * Copilot, Cursor, Antigravity, and other tools default to sequential.
 */
export function detectOrchestrationMode(
  env: NodeJS.ProcessEnv = process.env,
  hasClaudeDir = false
): OrchestrationMode {
  const isClaudeEnv =
    typeof env['ANTHROPIC_API_KEY'] === 'string' ||
    Object.keys(env).some((key) => key.startsWith('CLAUDE_')) ||
    hasClaudeDir;

  return isClaudeEnv ? 'parallel' : 'sequential';
}

/**
 * Describe the active orchestration mode for display in CLI output.
 */
export function describeMode(mode: OrchestrationMode): string {
  if (mode === 'parallel') {
    return 'parallel (Claude-detected; independent tasks may run concurrently)';
  }
  return 'sequential (all tasks run one at a time; parallel gates disabled)';
}

/**
 * Return whether parallel execution is allowed for independent chapter tasks
 * under the given mode.
 */
export function isParallelAllowed(mode: OrchestrationMode): boolean {
  return mode === 'parallel';
}
