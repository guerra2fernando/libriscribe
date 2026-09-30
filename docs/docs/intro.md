---
sidebar_position: 1
---

# Introduction to LibriScribe

LibriScribe is an AI-powered book writing assistant designed to streamline the creative process. It uses a multi-agent architecture, with each agent specialized in a particular task. It now supports three setup flows: Simple Guided Setup, Advanced Guided Setup, and Expert configuration files for repeatable runs and deeper customization.

## Core Concepts

LibriScribe is built around the idea of a **multi-agent system**.  Each agent is a Python class responsible for a specific aspect of the book writing process.  This modular design makes the project extensible and easier to maintain.

## Agents

Here's a brief overview of the key agents:

*   **`ProjectManagerAgent`:**  Manages the overall workflow and coordinates the other agents.  This is the main interface for the command-line tool.
*   **`ConceptGeneratorAgent`:**  Generates initial book concepts, including title, logline, and a detailed description.
*   **`OutlinerAgent`:**  Creates a comprehensive chapter-by-chapter outline for the book.
*   **`CharacterGeneratorAgent`:**  Generates detailed character profiles, including background, personality, and relationships.
*   **`WorldbuildingAgent`:**  Creates detailed worldbuilding information (history, culture, geography, etc.) relevant to the book's genre and setting.
*   **`ChapterWriterAgent`:**  Writes the first draft of a chapter scene-by-scene, with narrative constraint injection and quality loop.
*   **`EditorAgent`:**  Refines and edits a chapter, focusing on clarity, consistency, grammar, and style.
*   **`StyleEditorAgent`:** Refines the chapter's writing style based on specified tone and target audience preferences.
*   **`ContentReviewerAgent`:** Reviews chapter content for consistency, clarity, and plot holes.
*   **`FactCheckerAgent`:**  (Primarily for non-fiction) Verifies factual claims made within a chapter.
*   **`PlagiarismCheckerAgent`:**  Identifies potential plagiarism issues in a chapter.
*   **`ResearcherAgent`:**  Conducts web research on a specified topic and provides a summary of findings.
*   **`FormattingAgent`:**  Combines all generated chapters into a single, well-formatted Markdown or PDF document.

## Narrative Quality Layer

LibriScribe 0.5.0 includes three systems that close the loop between writing and quality automatically:

*   **`NarrativeGraphBuilder`:** Extracts structured narrative facts (entities, predicates, values) from each chapter after it is written. Facts are persisted in `narrative_graph.json` and survive partial runs.
*   **`InvariantChecker`:** Before each scene is generated, detects hard and soft violations (dead characters reappearing, physical actions by injured characters, destroyed locations revisited) and injects a `NARRATIVE CONSTRAINTS:` block into the scene prompt.
*   **`ContentQualityAgent`:** Scores prose across 5 axes — cliche density, show-don't-tell ratio, dialogue voice consistency, sentence variety, and scene function clarity. Operates in two modes:
    *   **Option A (Preventive):** Prior-chapter quality flags injected into the next chapter's scene prompts as `STYLE CONSTRAINTS:`.
    *   **Option B (Reactive):** Per-scene inline rewrite when the overall score falls below 0.65, targeting only the flagged issues while preserving all plot facts.

## Getting Started

See the [Installation Guide](./getting-started) for detailed instructions on setting up LibriScribe.

## Usage

The [Usage Guide](./usage) explains the current CLI workflow, including Simple, Advanced, and Expert modes, plus provider defaults, project-level model overrides, and per-agent model selection.
