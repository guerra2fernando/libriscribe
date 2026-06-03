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

    # Retrieval Defaults
    retrieval_enabled: bool = False
    retrieval_default_mode: str = "disabled"
    retrieval_backend: str = "local"
    retrieval_embedding_provider: str = "sentence-transformers"
    retrieval_embedding_model: str = "all-MiniLM-L6-v2"
    retrieval_chroma_path: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    mongodb_vector_uri: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""
    weaviate_url: str = ""
    weaviate_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")  # type: ignore

