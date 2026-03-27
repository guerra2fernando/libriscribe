/**
 * force-policy — shared destructive-action guard for all CLI commands.
 *
 * Centralizes the pattern of:
 *   1. Print a warning describing the destructive action.
 *   2. Require explicit acknowledgment (interactive prompt or --yes flag).
 *   3. Return whether the user confirmed.
 *
 * Force flags never bypass mandatory approval gates for workflow stage transitions.
 */
import chalk from 'chalk';
import inquirer from 'inquirer';

/** Options passed to the guard. */
export interface ForceGuardOptions {
  /** Human-readable description of what will be destroyed / overwritten. */
  action: string;
  /** Paths or items that will be affected, printed as a bullet list. */
  targets: string[];
  /** If true, skip the interactive prompt and confirm automatically (CI use). */
  autoYes?: boolean;
}

/**
 * Print a destructive-action warning and ask the user for confirmation.
 *
 * Returns true if the user confirmed (or autoYes was set).
 * Returns false if the user declined.
 */
export async function requireForceConfirmation(opts: ForceGuardOptions): Promise<boolean> {
  console.log('');
  console.log(chalk.yellow('⚠  DESTRUCTIVE ACTION'));
  console.log(chalk.yellow('─'.repeat(50)));
  console.log(chalk.white(opts.action));
  console.log('');
  console.log(chalk.dim('Affected paths:'));
  for (const t of opts.targets) {
    console.log(chalk.dim(`  • ${t}`));
  }
  console.log('');

  if (opts.autoYes) {
    console.log(chalk.dim('(--yes flag set — auto-confirming)'));
    return true;
  }

  const { confirmed } = await inquirer.prompt<{ confirmed: boolean }>([
    {
      type: 'confirm',
      name: 'confirmed',
      message: 'Are you sure you want to proceed?',
      default: false,
    },
  ]);

  return confirmed;
}

/**
 * Abort with an error message when a force-protected operation is attempted
 * without the --force flag.
 */
export function rejectWithoutForce(description: string): never {
  console.error(chalk.red(`✗  ${description}`));
  console.error(chalk.dim('  Run with --force to override.'));
  process.exit(1);
}
