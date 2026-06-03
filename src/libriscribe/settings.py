# src/libriscribe/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    openai_api_key: str = ""  # Optional, can be empty
    google_ai_studio_api_key: str = ""
    claude_api_key: str = ""
    deepseek_api_key: str = ""
    mistral_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-3-haiku"
    projects_dir: str = str(Path(__file__).parent.parent.parent / "projects")
    default_llm: str = "openai" # Set a default

    model_config = SettingsConfigDict(env_file=".env", extra='ignore') # type: ignore