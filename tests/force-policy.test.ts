/**
 * Tests for force-policy: rejectWithoutForce behavior.
 * requireForceConfirmation is not unit-tested here as it's interactive (inquirer).
 */
import { describe, it, expect } from 'vitest';
import { rejectWithoutForce } from '../src/lib/force-policy.js';

describe('rejectWithoutForce', () => {
  it('throws a process.exit by calling process.exit(1)', (): void => {
    // We capture process.exit to avoid actually exiting the test process
    const originalExit = process.exit.bind(process);
    let exitCode: number | undefined;

    // @ts-expect-error: override for testing
    process.exit = (code: number): never => {
      exitCode = code;
      throw new Error('process.exit called');
    };

    try {
      rejectWithoutForce('test destructive action');
    } catch {
      // expected — we throw to prevent actual exit
    } finally {
      // @ts-expect-error: restore original
      process.exit = originalExit;
    }

    expect(exitCode).toBe(1);
  });
});
