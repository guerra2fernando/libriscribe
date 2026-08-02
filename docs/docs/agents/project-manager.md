---
sidebar_position: 1
---

# Project Manager Agent

The Project Manager Agent is the central coordinator of LibriScribe's book writing process. It manages the workflow and orchestrates the interactions between all other agents.

## Overview

The Project Manager Agent serves as the main interface between the user and LibriScribe's various specialized agents. It handles project initialization, coordinates the execution of different writing stages, manages the overall book creation process, and exposes the Narrative Quality Layer methods.

## Key Responsibilities

- **Project Initialization**: Creates and configures new book projects
- **Workflow Management**: Coordinates the sequence of agent operations
- **Resource Management**: Handles file organization and agent communication
- **Process Oversight**: Monitors and reports on the progress of book creation
- **Narrative Quality**: Exposes `analyze_quality`, `update_narrative_graph`, and `check_narrative_violations` methods

## Command Interface

The Project Manager is primarily surfaced through the guided CLI flow:

```bash
libriscribe start
```

After initialization, the main follow-up commands are:

```bash
# Generate book outline
libriscribe outline

# Generate character profiles
libriscribe characters

# Create worldbuilding details
libriscribe worldbuilding

# Write a specific chapter
libriscribe write --chapter-number 1

# Edit a specific chapter
libriscribe edit --chapter-number 1

# Format the final manuscript
libriscribe format

# Conduct research
libriscribe research --query "your topic"

# Resume an existing project
libriscribe resume --project-name your_project

# Narrative Quality Layer commands
libriscribe narrative rebuild --project your_project
libriscribe narrative check your_project --chapter 2
libriscribe quality your_project --chapter 1
```

## Narrative Quality Methods

### `analyze_quality(chapter_number)`

Runs `ContentQualityAgent` on the specified chapter and prints a bar-chart of the 5 quality axis scores to the console. Saves results to `quality_chapter_{N}.json`.

### `update_narrative_graph(chapter_number)`

Runs `NarrativeGraphBuilder.extract_from_chapter()` and logs the number of new facts extracted. Used internally after each chapter is written, and exposed via `narrative rebuild` CLI.

### `check_narrative_violations(chapter_number)`

Loads `narrative_graph.json`, runs `InvariantChecker` on all scenes in the specified chapter, and prints any hard or soft violations to the console. Used via `narrative check` CLI.

## File Structure

The Project Manager creates and maintains the following project structure:

```
project_name/
├── project_data.json          # Project configuration and metadata
├── .libriscribe_status.json   # Stage/checkpoint recovery state
├── outline.md                 # Book outline
├── characters.json            # Character profiles
├── world.json                 # Worldbuilding details
├── chapter_1.md               # Individual chapter files
├── chapter_2.md
├── narrative_graph.json       # Persistent narrative facts
├── quality_chapter_1.json     # Prose quality report for chapter 1
└── quality_chapter_2.json     # Prose quality report for chapter 2
```

## Error Handling

The Project Manager implements comprehensive error handling:
- Validates project initialization parameters
- Ensures required files exist before agent execution
- Logs errors and provides user-friendly error messages
- Maintains project consistency during failures

## Integration with Other Agents

The Project Manager seamlessly integrates with all other LibriScribe agents:
- Passes necessary context between agents
- Ensures proper sequencing of operations
- Manages file dependencies
- Coordinates multi-agent operations
