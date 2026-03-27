/**
 * book-producer CLI — command router.
 * 
 * USAGE:
 * - `book-producer install` (required, terminal only)
 * - All other commands are optional; they are provided as CLI convenience shortcuts.
 * 
 * CHAT-FIRST WORKFLOW (primary):
 * After install, work entirely in your AI tool of choice. The agent reads/writes
 * .spec/<book-idea>/ files directly.
 * No additional CLI commands needed. Stages 1–6 run conversationally; user approvals happen in chat.
 * 
 * CLI SHORTCUTS (optional):
 * Use `init`, `list`, `use`, `doctor`, `refresh`, and `orchestrate` if you prefer
 * terminal workflow or need maintenance tasks.
 */
import { Command } from 'commander';
import { installCommand } from './commands/install.js';
import { initCommand } from './commands/init.js';
import { statusCommand } from './commands/status.js';
import { listCommand } from './commands/list.js';
import { useCommand } from './commands/use.js';
import { doctorCommand } from './commands/doctor.js';
import { refreshCommand } from './commands/refresh.js';
import { orchestrateCommand } from './commands/orchestrate.js';

const program = new Command();

program
  .name('book-producer')
  .description('Multi-tool book creation framework')
  .version('0.1.0');

program.addCommand(installCommand());
program.addCommand(initCommand());
program.addCommand(statusCommand());
program.addCommand(listCommand());
program.addCommand(useCommand());
program.addCommand(doctorCommand());
program.addCommand(refreshCommand());
program.addCommand(orchestrateCommand());

program.parse(process.argv);
