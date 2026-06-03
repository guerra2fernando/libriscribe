---
sidebar_position: 1
---

# Project Manager Agent

The Project Manager Agent is the central coordinator of LibriScribe's book writing process. It manages the workflow and orchestrates the interactions between all other agents.

## Overview

The Project Manager Agent serves as the main interface between the user and LibriScribe's various specialized agents. It handles project initialization, coordinates the execution of different writing stages, and manages the overall book creation process.

## Key Responsibilities

- **Project Initialization**: Creates and configures new book projects
- **Workflow Management**: Coordinates the sequence of agent operations
- **Resource Management**: Handles file organization and agent communication
- **Process Oversight**: Monitors and reports on the progress of book creation

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
```

Concept generation, chapter review, style editing, and other internal stages are commonly coordinated automatically by the Project Manager during guided setup.

## File Structure

The Project Manager creates and maintains the following project structure:

```
project_name/
├── project_data.json     # Project configuration and metadata
├── outline.md           # Book outline
├── characters.json      # Character profiles
├── world.json          # Worldbuilding details
├── chapter_1.md        # Individual chapter files
├── chapter_2.md
└── ...
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