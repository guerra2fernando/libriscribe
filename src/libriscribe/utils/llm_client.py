# src/libriscribe/utils/llm_client.py
import openai
from openai import OpenAI  # For OpenAI
import logging
from tenacity import retry, stop_after_attempt, wait_random_exponential
from libriscribe.settings import Settings

import anthropic  # For Claude
import google.generativeai as genai  # For Google AI Studio
import requests  # For DeepSeek and Mistral

# ADDED THIS: Import the function
from libriscribe.utils.file_utils import extract_json_from_markdown

logger = logging.getLogger(__name__)

# Configure httpx logger to be less verbose
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)  # Or ERROR, to suppress even warnings


class LLMClient:
from libriscribe.utils.cost_tracker import CostTracker
    """Unified LLM client for multiple providers."""

    def __init__(self, llm_provider: str):
        self.cost_tracker = CostTracker()
        self.settings = Settings()
        self.llm_provider = llm_provider
        self.client = self._get_client()  # Initialize the correct client
        self.model = self._get_default_model()

    def _get_client(self):
        """Initializes the appropriate client based on the provider."""
        if self.llm_provider == "openrouter":
            return OpenAI(
                api_key=self.settings.openrouter_api_key,
                base_url=self.settings.openrouter_base_url,
            )
        elif self.llm_provider == "openai" or self.llm_provider == "openrouter":
            if not self.settings.openai_api_key:
                raise ValueError("OpenAI API key is not set.")
            return OpenAI(api_key=self.settings.openai_api_key)
        elif self.llm_provider == "claude":
            if not self.settings.claude_api_key:
                raise ValueError("Claude API key is not set.")
            return anthropic.Anthropic(api_key=self.settings.claude_api_key)
        elif self.llm_provider == "google_ai_studio":
            if not self.settings.google_ai_studio_api_key:
                raise ValueError("Google AI Studio API key is not set.")
            genai.configure(api_key=self.settings.google_ai_studio_api_key)
            return genai  # We don't instantiate a client, we use the module directly
        elif self.llm_provider == "deepseek":
            if not self.settings.deepseek_api_key:
                raise ValueError("DeepSeek API key is not set.")
            return None  # No client object, we'll use requests directly
        elif self.llm_provider == "mistral":
            if not self.settings.mistral_api_key:
                raise ValueError("Mistral API key is not set")
            return None
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def _get_default_model(self):
        """Gets the default model name for the selected provider."""
        if self.llm_provider == "openrouter":
            return self.settings.openrouter_model
        elif self.llm_provider == "openai" or self.llm_provider == "openrouter":
            return "gpt-4o-mini"
        elif self.llm_provider == "claude":
            return "claude-3-opus-20240229"  # Or another appropriate Claude 3 model
        elif self.llm_provider == "google_ai_studio":
            return "gemini-1.5-pro-002"
        elif self.llm_provider == "deepseek":
            return "deepseek-coder-6.7b-instruct"
        elif self.llm_provider == "mistral":
            return "mistral-medium-latest"
        else:
            return "unknown"  # Should not happen, but good for safety

    def set_model(self, model_name: str):
        self.model = model_name

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    def generate_content(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        operation: str = "generate_content"
    ) -> Optional[str]:
        """Generate content using the configured LLM with cost tracking."""
        input_tokens = len(prompt.split()) * 1.3  # Rough estimate
        
        try:
            if self.llm_provider == "openai" or self.llm_provider == "openrouter":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                response_text = response.choices[0].message.content
                
                # Track actual usage if available
                if hasattr(response, "usage"):
                    actual_input = response.usage.prompt_tokens
                    actual_output = response.usage.completion_tokens
                else:
                    actual_input = int(input_tokens)
                    actual_output = len(response_text.split()) * 1.3
                
            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                actual_input = getattr(response.usage, "input_tokens", int(input_tokens))
                actual_output = getattr(response.usage, "output_tokens", len(response_text.split()) * 1.3)
                
            else:
                # Other providers - existing code with estimates
                response_text = self._handle_other_providers(prompt, max_tokens, temperature)
                actual_input = int(input_tokens)
                actual_output = len(response_text.split()) * 1.3 if response_text else 0
            
            # Log usage
            model_key = f"{self.llm_provider}/{self.model}"
            cost = self.cost_tracker.calculate_cost(model_key, actual_input, actual_output)
            self.cost_tracker.log_usage(
                self.llm_provider, self.model, operation,
                int(actual_input), int(actual_output), cost
            )
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return None
            else:
                repair_prompt = f"You are a helpful AI that only returns valid JSON.  Fix the following broken JSON:\n\n```json\n{response_text}\n```"
                repaired_response = self.generate_content(
                    repair_prompt, max_tokens=max_tokens, temperature=0.2
                )  # Low temp for corrections
                if repaired_response:
                    repaired_json = extract_json_from_markdown(repaired_response)
                    if repaired_json is not None:
                        # CRITICAL CHANGE:  Return the JSON *string*, not wrapped in Markdown.
                        return repaired_response
        logger.error("JSON repair failed.")
        return ""  # Return empty
