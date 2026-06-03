# src/libriscribe/settings.py
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""  # Optional, can be empty
    openai_model: str = "gpt-4o-mini"
    google_ai_studio_api_key: str = ""
    google_ai_studio_model: str = "gemini-2.5-flash"
    claude_api_key: str = ""
    claude_model: str = "claude-3-opus-20240229"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-coder-6.7b-instruct"
    mistral_api_key: str = ""
    mistral_model: str = "mistral-medium-latest"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-3-haiku"
    fallback_chain: str = ""
    projects_dir: str = str(Path(__file__).parent.parent.parent / "projects")
    default_llm: str = "openai"  # Set a default

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")  # type: ignore
