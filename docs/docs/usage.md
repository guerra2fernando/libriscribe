---
sidebar_position: 3
---

# Usage Guide

This guide explains the current LibriScribe CLI workflow and how model selection behaves across setup modes.

## Running LibriScribe

Start the interactive setup flow with:

```bash
libriscribe start
```

Or jump directly into Expert mode with a config file:

```bash
libriscribe start --config examples/expert-config.yaml
```

## Setup Modes

LibriScribe now offers three setup modes:

### 1. Simple Guided Setup

Simple mode is optimized for speed. It asks for the core project information and uses the selected provider's default model from `.env` automatically.

Best for:
- fast first drafts
- minimal decision-making
- users who want provider defaults to do the work

### 2. Advanced Guided Setup

Advanced mode gives you more control over book structure and generation choices while keeping the workflow guided.

In addition to the normal project questions, Advanced mode lets you choose whether to:
- use the selected provider's default model from `.env`
- or enter one custom model ID for the project

Best for:
- users who want one project-wide model override
- users who still prefer an interactive setup flow

### 3. Expert: Configuration File

Expert mode loads a JSON or YAML config file and supports the most control.

Expert mode can define:
- the provider with `project.llm_provider`
- a project-wide model with `project.model`
- per-agent model overrides with `project.agent_models`
- workflow automation preferences
- whether chapter writing pauses between chapters or runs across the whole book automatically
- whether chapter failures should stop the run or continue to the next chapter
- output and formatting preferences

Best for:
- repeatable runs
- automation
- power users
- different models for different agents

## Model Selection Behavior

LibriScribe resolves models in this order:

1. `project.agent_models[agent_name]` in Expert mode
2. `project.model` for the project
3. provider default from `.env`

That means you can start simple with `.env`, move to one custom project model in Advanced mode, and graduate to per-agent control in Expert mode without changing the overall workflow style.

When full-book automatic writing is enabled, LibriScribe still keeps one summary confirmation before it starts, including a warning that the run may consume many tokens / credits.

## Typical Flow

A typical full run looks like this:

1. initialize the project
2. generate/refine the concept
3. generate the outline
4. optionally generate characters
5. optionally generate worldbuilding
6. write chapters
7. review/edit chapters
8. format the manuscript

## Useful CLI Commands After Setup

Once a project is initialized, the CLI also exposes focused commands for later stages:

- `libriscribe outline`
- `libriscribe characters`
- `libriscribe worldbuilding`
- `libriscribe write`
- `libriscribe edit`
- `libriscribe format`
- `libriscribe research`
- `libriscribe resume`

These commands are useful if you want to continue working on a project after the initial guided setup.
