import { describe, it, expect } from 'vitest';
import { buildChapterPlan, buildResearchPlan, resolveExecutionMode } from '../src/lib/work-orchestrator.js';

describe('resolveExecutionMode', () => {
  it('uses parallel packets for Claude', () => {
    expect(resolveExecutionMode('claude')).toBe('parallel');
  });

  it('uses sequential packets for non-Claude tools', () => {
    expect(resolveExecutionMode('cursor')).toBe('sequential');
    expect(resolveExecutionMode('copilot')).toBe('sequential');
    expect(resolveExecutionMode('antigravity')).toBe('sequential');
  });
});

describe('buildChapterPlan', () => {
  it('creates one packet per chapter for Claude', () => {
    const plan = buildChapterPlan('my-book', [3, 1], 'claude', 'parallel');
    expect(plan.executionMode).toBe('parallel');
    expect(plan.packets).toHaveLength(2);
    expect(plan.packets[0]?.id).toBe('chapter-1');
    expect(plan.packets[1]?.id).toBe('chapter-3');
  });

  it('creates a serialized packet for non-Claude tools', () => {
    const plan = buildChapterPlan('my-book', [2, 4], 'copilot', 'sequential');
    expect(plan.executionMode).toBe('sequential');
    expect(plan.packets).toHaveLength(1);
    expect(plan.packets[0]?.id).toBe('chapter-sequence');
  });
});

describe('buildResearchPlan', () => {
  it('creates one research packet per topic for Claude', () => {
    const plan = buildResearchPlan('my-book', ['timeline', 'history'], 'claude', 'parallel');
    expect(plan.executionMode).toBe('parallel');
    expect(plan.packets).toHaveLength(2);
  });

  it('creates a serialized research packet for non-Claude tools', () => {
    const plan = buildResearchPlan('my-book', ['timeline', 'history'], 'cursor', 'sequential');
    expect(plan.executionMode).toBe('sequential');
    expect(plan.packets).toHaveLength(1);
    expect(plan.packets[0]?.id).toBe('research-sequence');
  });
});
