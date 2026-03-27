/**
 * Tests for orchestration mode detection and description.
 */
import { describe, it, expect } from 'vitest';
import {
  detectOrchestrationMode,
  describeMode,
  isParallelAllowed,
} from '../src/lib/orchestration.js';

describe('detectOrchestrationMode', () => {
  it('returns sequential when no Claude signals present', () => {
    expect(detectOrchestrationMode({}, false)).toBe('sequential');
  });

  it('returns parallel when ANTHROPIC_API_KEY is set', () => {
    expect(detectOrchestrationMode({ ANTHROPIC_API_KEY: 'sk-test' }, false)).toBe('parallel');
  });

  it('returns parallel when any CLAUDE_ env var is set', () => {
    expect(detectOrchestrationMode({ CLAUDE_PROJECT_ID: 'abc' }, false)).toBe('parallel');
  });

  it('returns parallel when .claude/ directory exists', () => {
    expect(detectOrchestrationMode({}, true)).toBe('parallel');
  });

  it('returns sequential when only unrelated env vars are set', () => {
    expect(detectOrchestrationMode({ OPENAI_API_KEY: 'sk-abc', PATH: '/usr/bin' }, false)).toBe('sequential');
  });
});

describe('describeMode', () => {
  it('mentions parallel for parallel mode', () => {
    expect(describeMode('parallel')).toContain('parallel');
  });

  it('mentions sequential for sequential mode', () => {
    expect(describeMode('sequential')).toContain('sequential');
  });
});

describe('isParallelAllowed', () => {
  it('returns true for parallel mode', () => {
    expect(isParallelAllowed('parallel')).toBe(true);
  });

  it('returns false for sequential mode', () => {
    expect(isParallelAllowed('sequential')).toBe(false);
  });
});
