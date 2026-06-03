# LibriScribe 📚✨

<div align="center">

<img src="https://guerra2fernando.github.io/libriscribe/img/logo.png" alt="LibriScribe Logo" width="30%">

### Your AI-Powered Multi-Agent Book Writing Assistant

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-visit%20now-green.svg)](https://guerra2fernando.github.io/libriscribe/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-supported-purple.svg)](https://openrouter.ai/)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow.svg?style=flat&logo=buy-me-a-coffee)](https://buymeacoffee.com/guerra2fernando)

</div>

---

## 🌟 Overview

**LibriScribe** revolutionizes book writing through a sophisticated multi-agent system. Specialized AI agents collaborate seamlessly to assist you from initial brainstorms and worldbuilding to draft generation, interactive editing, and local publication. 

With our latest integration updates, LibriScribe supports **OpenRouter routing**, fully customizable **external YAML prompts**, automated **LLM cost tracking**, and a **self-healing JSON parser** for unmatched writing reliability.

![Libriscribe Demo](https://github.com/guerra2fernando/libriscribe/blob/main/docs/static/img/libriscribe.gif?raw=true)

---

## 🏗️ Multi-Agent Architecture

LibriScribe orchestrates specialized agents guided by your configuration, loading prompts externally and logging execution costs automatically:

```mermaid
graph TD
    User([User CLI / Prompt]) --> PM[Project Manager Agent]
    PM --> PL[Prompt Loader]
    PL -. Loads YAML Templates .-> Templates[(prompts/templates/)]
    
    PM --> CG[Concept Generator]
    PM --> OL[Outliner]
    PM --> CH[Character Generator]
    PM --> WB[Worldbuilder]
    PM --> CW[Chapter Writer]
    PM --> ED[Editor]
    
    CW & ED --> LLM[Unified LLM Client]
    LLM --> CT[Cost Tracker]
    CT --> Log[(llm_usage.jsonl)]
    
    PM --> FA[Optimized Formatting Agent]
    FA -. Local Compilation .-> Manuscript([manuscript.md / PDF])
    
    style PM fill:#2563EB,stroke:#1D4ED8,color:#FFFFFF,stroke-width:2px
    style FA fill:#059669,stroke:#047857,color:#FFFFFF,stroke-width:2px
    style CT fill:#DC2626,stroke:#B91C1C,color:#FFFFFF,stroke-width:2px
```

---

## ✨ Features

### 1. Unified LLM & OpenRouter Routing 🤖
*   **Multi-Provider Support:** Run on **OpenAI**, **Anthropic Claude**, **Google Gemini**, **DeepSeek**, **Mistral**, or any provider supported by **OpenRouter**.
*   **Intelligent Auto-Formatting:** Built-in JSON post-processing wrapper guarantees clean responses when routing through diverse models.
*   **Full Backward Compatibility:** Swap models dynamically without breaking existing templates or agent behaviors.

### 2. External YAML Prompt Templates 📝
*   **Fully Customizable Prompts:** 15 comprehensive agent templates isolated in `prompts/templates/`. Customize AI personas, vocabulary, and styles without editing python code.
*   **Dynamic Loading:** Auto-detects custom prompt modifications and falls back gracefully to hardcoded prompts if any files are missing.
*   **Genre-Specific Personas:** Easily configure suspense, scientific accuracy, or business tones directly inside templates.

### 3. LLM Cost Optimization & Tracking 💰
*   **Automatic Usage Logging:** Track execution metrics in `llm_usage.jsonl`. Logs timestamps, providers, selected models, precise input/output token counts, and USD cost calculations.
*   **Cost-Optimized Formatting Agent:** The compiler works **entirely locally** using local Markdown parsing and title-page assembly. This bypasses expensive LLM formatting calls, **saving ~$2.40 per manuscript!**
*   **Suggested Models Tiers:** Define high, medium, or low-cost model suggestions right inside prompt template settings.

### 4. Enterprise-Grade JSON Robustness 🔐
*   **Self-Healing AI Responses:** Automated prompt-repair attempts logic if raw JSON parse initially fails, ensuring agents heal malformed responses.
*   **f-String Safe Templates:** Fixed escaping issues to prevent code integration errors during runtime formatting.

### 5. Creative Writing & QA Suite 🎨
*   **Automated Outlining & Concept Creation:** Turn standard premises into rich narrative blueprints.
*   **Worldbuilding & Character Generation:** Generate complex multi-dimensional character profiles and coherent cultures.
*   **Chapter Writing & Refining:** Continuous draft-review cycles via an expert editing loops.

---

## 🚀 Quickstart

### 1. Installation

Clone and install LibriScribe locally:
```bash
git clone https://github.com/guerra2fernando/libriscribe.git
cd libriscribe
pip install -e .
```

### 2. Configuration

Create a `.env` file in the root directory and enter your API keys for the providers you wish to use:

```env
# Standard Providers
OPENAI_API_KEY=your_openai_key_here
GOOGLE_AI_STUDIO_API_KEY=your_google_key_here
CLAUDE_API_KEY=your_claude_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
MISTRAL_API_KEY=your_mistral_key_here

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3-haiku
```

### 3. Launch

To start the interactive prompt runner:
```bash
libriscribe start
```

Choose between:
*   🎯 **Simple Guided Setup:** Quick, streamlined guided book generation.
*   🎛️ **Advanced Guided Setup:** Fine-grained control over tone, target audience, and precise chapter goals.
*   ⚙️ **Expert: Configuration File:** Load a JSON or YAML setup file for repeatable, highly customizable runs.

You can also jump straight into Expert mode from the CLI:
```bash
libriscribe start --config examples/expert-config.yaml
```

---

## 💻 Customizing Prompts

You can easily adjust the tone and focus of any writing agent. For example, to create a specialized Mystery Editor:

1.  Copy the default editor template:
    ```bash
    cp prompts/templates/editor.yml prompts/templates/my-editor.yml
    ```
2.  Edit `prompts/templates/editor.yml` to specify custom instructions and cost settings:
    ```yaml
    name: "Mystery Editor"
    cost_tier: "medium"
    settings:
      max_tokens: 4000
      suggested_models: ["openai/gpt-4o-mini", "anthropic/claude-3-5-sonnet"]
    template: |
      You are an expert mystery editor refining Chapter {chapter_number} of "{book_title}".
      Review content and emphasize clue placement, suspense, and red herrings.
      
      Feedback to address: {review_feedback}
      Chapter: {chapter_content}
    ```

The agent will automatically load and apply your customized template on its next run!

---

## ⚙️ Expert Configuration Files

Expert mode supports both JSON and YAML configuration files so repeat runs can be automated and reused.
LibriScribe also remembers the most recent expert settings and can offer them again on the next Expert run.

Expert mode currently supports:

- `libriscribe start --config <path>` for direct config-driven startup
- JSON and YAML project definitions
- reusable starter files in `examples/`
- workflow-stage controls for:
  - concept approval
  - outline review
  - character generation
  - worldbuilding generation
  - chapter writing
  - formatting and output format
- persisted recent expert settings in `.libriscribe_last_config.json`

Example:

```yaml
version: 1
project:
  project_name: my_fantasy_novel
  title: The Last Ember Gate
  category: Fiction
  genre: Fantasy
  language: English
  description: An exiled archivist discovers a buried gate tied to a fallen empire.
  num_characters: "3"
  worldbuilding_needed: true
  review_preference: AI
  book_length: Novel
  tone: Serious
  target_audience: Young Adult
  num_chapters: "10"
  llm_provider: openai
workflow:
  concept_approval: auto
  outline_review: prompt
  character_generation: auto
  worldbuilding_generation: auto
  chapter_writing: prompt
  formatting: auto
  output_format: markdown
```

Starter files are available in:

- `examples/expert-config.json`
- `examples/expert-config.yaml`

---

## 📁 Project Structure

A typical project created by LibriScribe looks like this:

```
your_project/
├── project_data.json    # Project metadata & configurations
├── outline.md          # Generated chapter-by-chapter outline
├── characters.json     # Multi-dimensional character profiles
├── world.json         # Worldbuilding details (category-specific)
├── chapter_1.md       # Generated and polished chapter drafts
├── chapter_2.md
└── research_results.md # Research findings
```

All global execution costs and API calls are written directly to your workspace:
*   📂 `llm_usage.jsonl` - Real-time spend tracking and performance logging.
*   📂 `prompts/templates/` - External YAML files for 15+ specialized prompts.

---

## 🗺️ LibriScribe Development Roadmap

### 🤖 LLM Integration & Support
- [x] **Multi-LLM Support**: Anthropic Claude, Google Gemini, DeepSeek, Mistral, OpenAI
- [x] **Unified OpenRouter Gateway Integration**
- [x] **Cost Optimization Engine** (`llm_usage.jsonl` tracking + local manuscript compilation)
- [x] **Response Quality & Self-Healing JSON Parser**
- [ ] **Automatic Model Fallback System**
- [ ] **Model Performance Benchmarking**

### 🔍 Vector Store & Search Enhancement
- [ ] **Multi-Vector Database Support**: ChromaDB, MongoDB Vector Search, Pinecone, Weaviate
- [ ] **Advanced Search Features**: Semantic Search, Hybrid Search (Keywords + Semantic), Cross-Reference Search
- [ ] **Embedding Models Integration**: Multiple Embedding Model Support, Custom Embedding Training

### 🔐 Authentication & Authorization
- [ ] **Cerbos Implementation**: Role-Based Access Control (RBAC), Attribute-Based Access Control (ABAC)
- [ ] **User Management System**: User Registration, Social Auth, Multi-Factor Auth, Session Management
- [ ] **Security Features**: Audit Logging, Rate Limiting, API Key Management

---

## 🤝 Contributing

We welcome contributions! Check out our [Contributing Guidelines](CONTRIBUTING.md) to get started.

```bash
# Verify imports and setup successfully before submitting a PR
PYTHONPATH=src python -c 'import libriscribe.main'
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by Fernando Guerra and Lenxys

[⭐ Star us on GitHub](https://github.com/guerra2fernando/libriscribe)

If LibriScribe has been helpful, consider buying me a coffee:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow.svg?style=flat&logo=buy-me-a-coffee)](https://buymeacoffee.com/guerra2fernando)

</div>
