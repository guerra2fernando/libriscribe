---
sidebar_position: 2
---

# Getting Started

This guide walks you through installing LibriScribe, configuring model defaults, and launching the CLI.

## Prerequisites

- **Python 3.10 or later:** Check with `python --version`.
- **pip:** Usually included with Python.
- **At least one LLM API key** from one of these providers:
  - **OpenAI:** [Get API Key](https://platform.openai.com/signup/)
  - **Anthropic:** [Get API Key](https://console.anthropic.com/)
  - **DeepSeek:** [Get API Key](https://platform.deepseek.com/)
  - **Google AI Studio (Gemini):** [Get API Key](https://aistudio.google.com/)
  - **Mistral AI:** [Get API Key](https://console.mistral.ai/)
  - **OpenRouter:** [Get API Key](https://openrouter.ai/)

## Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/guerra2fernando/libriscribe.git
   cd libriscribe
   ```

2. **Install LibriScribe**

   ```bash
   pip install -e .
   ```

   Editable install is convenient if you plan to customize prompts or work on the codebase locally.

3. **Create your `.env` file**

   Start from the provided example:

   ```bash
   cp .env.example .env
   ```

4. **Add API keys and optional model defaults**

   Example:

   ```env
   OPENAI_API_KEY=your_openai_key_here
   OPENAI_MODEL=gpt-4o-mini

   GOOGLE_AI_STUDIO_API_KEY=your_google_key_here
   GOOGLE_AI_STUDIO_MODEL=gemini-2.5-flash

   CLAUDE_API_KEY=your_claude_key_here
   CLAUDE_MODEL=claude-3-opus-20240229

   DEEPSEEK_API_KEY=your_deepseek_key_here
   DEEPSEEK_MODEL=deepseek-coder-6.7b-instruct

   MISTRAL_API_KEY=your_mistral_key_here
   MISTRAL_MODEL=mistral-medium-latest

   OPENROUTER_API_KEY=your_openrouter_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=anthropic/claude-3-haiku
   ```

   LibriScribe uses these model values as **provider defaults**:

   - **Simple Guided Setup** uses the selected provider's default model automatically.
   - **Advanced Guided Setup** lets you keep the `.env` default or enter a single custom model ID for the project.
   - **Expert mode** can override both the provider default and the project default through config files.

## Launching LibriScribe

Start the interactive CLI with:

```bash
libriscribe start
```

LibriScribe currently offers three setup flows:

- **Simple Guided Setup**
- **Advanced Guided Setup**
- **Expert: Configuration File**

You can also jump directly into Expert mode:

```bash
libriscribe start --config examples/expert-config.yaml
```

## Verifying the Installation

After installation, you can verify the CLI is available with:

```bash
libriscribe start --help
```