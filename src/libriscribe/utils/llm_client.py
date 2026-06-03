import logging
import re
from typing import Dict, Optional

import anthropic
import requests
from google import genai
from google.genai import types as google_genai_types
from openai import OpenAI

from libriscribe.settings import Settings
from libriscribe.utils.cost_tracker import CostTracker
from libriscribe.utils.file_utils import extract_json_from_markdown
from libriscribe.utils.model_routing import (
    ModelRoute,
    build_fallback_route_chain,
    get_default_model_for_provider,
    normalize_fallback_chain,
    parse_fallback_chain_string,
)

logger = logging.getLogger(__name__)

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)


class RecoverableLLMError(Exception):
    def __init__(self, failure_type: str, message: str):
        super().__init__(message)
        self.failure_type = failure_type


class LLMClient:
    """Unified LLM client for multiple providers with simple fallback routing."""

    def __init__(self, llm_provider: str):
        self.settings = Settings()
        self.llm_provider = llm_provider
        self._client_cache: Dict[str, object] = {}
        self.client = self._get_client_for_provider(llm_provider)
        self.default_model = self._get_default_model_for_provider(llm_provider)
        self.model = self.default_model
        self.cost_tracker = CostTracker()
        self.request_fallback_chain: Optional[list[str]] = None

    def _get_client_for_provider(self, provider: str):
        if provider in self._client_cache:
            return self._client_cache[provider]

        if provider == "openrouter":
            if not self.settings.openrouter_api_key:
                raise ValueError("OpenRouter API key is not set.")
            client = OpenAI(
                api_key=self.settings.openrouter_api_key,
                base_url=self.settings.openrouter_base_url,
            )
        elif provider == "openai":
            if not self.settings.openai_api_key:
                raise ValueError("OpenAI API key is not set.")
            client = OpenAI(api_key=self.settings.openai_api_key)
        elif provider == "claude":
            if not self.settings.claude_api_key:
                raise ValueError("Claude API key is not set.")
            client = anthropic.Anthropic(api_key=self.settings.claude_api_key)
        elif provider == "google_ai_studio":
            if not self.settings.google_ai_studio_api_key:
                raise ValueError("Google AI Studio API key is not set.")
            client = genai.Client(api_key=self.settings.google_ai_studio_api_key)
        elif provider == "deepseek":
            if not self.settings.deepseek_api_key:
                raise ValueError("DeepSeek API key is not set.")
            client = None
        elif provider == "mistral":
            if not self.settings.mistral_api_key:
                raise ValueError("Mistral API key is not set.")
            client = None
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        self._client_cache[provider] = client
        return client

    def _get_default_model_for_provider(self, provider: str) -> str:
        return get_default_model_for_provider(provider, self.settings)

    def set_model(self, model_name: str):
        self.model = model_name

    def reset_model(self):
        self.model = self.default_model

    def set_fallback_chain(self, fallback_chain: Optional[list[str]]):
        if fallback_chain is None:
            self.request_fallback_chain = None
            return
        self.request_fallback_chain = normalize_fallback_chain(fallback_chain)

    def _get_active_fallback_chain(self) -> list[str]:
        if self.request_fallback_chain is not None:
            return self.request_fallback_chain
        return parse_fallback_chain_string(self.settings.fallback_chain)

    def _prepare_prompt(self, prompt: str, language: str) -> str:
        if (
            "IMPORTANT: The content should be written entirely in" not in prompt
            and language != "English"
        ):
            return prompt + f"\n\nIMPORTANT: Generate the response in {language}."
        return prompt

    def _get_status_code(self, exc: Exception) -> Optional[int]:
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            return status_code

        response = getattr(exc, "response", None)
        if response is not None:
            response_status = getattr(response, "status_code", None)
            if isinstance(response_status, int):
                return response_status

        return None

    def _classify_exception(self, exc: Exception) -> str:
        if isinstance(exc, RecoverableLLMError):
            return exc.failure_type

        if isinstance(exc, requests.Timeout):
            return "timeout"

        status_code = self._get_status_code(exc)
        if status_code == 429:
            return "rate_limit"
        if status_code and 500 <= status_code < 600:
            return "provider_server_error"

        message = str(exc).lower()
        if "timeout" in message or "timed out" in message:
            return "timeout"
        if (
            "429" in message
            or "rate limit" in message
            or "too many requests" in message
        ):
            return "rate_limit"
        if "api key is not set" in message:
            return "provider_not_configured"
        if "500" in message or "502" in message or "503" in message or "504" in message:
            return "provider_server_error"

        return "unhandled_error"

    def _should_retry_same_route(self, failure_type: str) -> bool:
        return failure_type in {"timeout", "rate_limit", "provider_server_error"}

    def _should_fallback(self, failure_type: str) -> bool:
        return failure_type in {
            "timeout",
            "rate_limit",
            "provider_server_error",
            "empty_response",
            "invalid_json_after_repair",
            "provider_not_configured",
        }

    def _log_usage(self, provider: str, model: str, prompt: str, response_text: str):
        input_tokens = len(prompt.split()) * 1.3
        output_tokens = len(response_text.split()) * 1.3 if response_text else 0
        cost = self.cost_tracker.calculate_cost(
            f"{provider}/{model}",
            int(input_tokens),
            int(output_tokens),
        )
        self.cost_tracker.log_usage(
            provider,
            model,
            "generate_content",
            int(input_tokens),
            int(output_tokens),
            cost,
        )

    def _request_with_fallback(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        language: str = "English",
        require_valid_json: bool = False,
    ) -> str:
        prepared_prompt = self._prepare_prompt(prompt, language)
        routes = build_fallback_route_chain(
            primary_provider=self.llm_provider,
            primary_model=self.model or self.default_model,
            fallback_chain=self._get_active_fallback_chain(),
            settings=self.settings,
        )
        last_error: Optional[Exception] = None

        for route_index, route in enumerate(routes):
            for attempt in range(1, 3):
                try:
                    response_text = self._generate_once(
                        route,
                        prepared_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    if not response_text or not response_text.strip():
                        raise RecoverableLLMError(
                            "empty_response",
                            f"{route.label} returned an empty response.",
                        )

                    if require_valid_json:
                        json_data = extract_json_from_markdown(response_text)
                        if json_data is None:
                            repair_prompt = (
                                "You are a helpful AI that only returns valid JSON. "
                                "Fix the following broken JSON:\n\n"
                                f"```json\n{response_text}\n```"
                            )
                            repaired_response = self._generate_once(
                                route,
                                repair_prompt,
                                max_tokens=max_tokens,
                                temperature=0.2,
                            )
                            if (
                                repaired_response
                                and extract_json_from_markdown(repaired_response)
                                is not None
                            ):
                                response_text = repaired_response
                            else:
                                raise RecoverableLLMError(
                                    "invalid_json_after_repair",
                                    f"{route.label} returned invalid JSON after repair.",
                                )

                    if route_index > 0:
                        logger.warning(
                            "Fallback succeeded: using %s after previous route failure.",
                            route.label,
                        )
                    return response_text
                except Exception as exc:
                    last_error = exc
                    failure_type = self._classify_exception(exc)
                    logger.warning(
                        "LLM route %s failed on attempt %s (%s): %s",
                        route.label,
                        attempt,
                        failure_type,
                        exc,
                    )

                    if attempt < 2 and self._should_retry_same_route(failure_type):
                        continue

                    has_next_route = route_index < len(routes) - 1
                    if has_next_route and self._should_fallback(failure_type):
                        next_route = routes[route_index + 1]
                        logger.warning(
                            "Falling back from %s to %s due to %s.",
                            route.label,
                            next_route.label,
                            failure_type,
                        )
                        break

                    logger.error(
                        "LLM generation failed for %s with no further fallback available.",
                        route.label,
                    )
                    return ""

        if last_error:
            logger.error(
                "LLM generation failed after exhausting fallback routes: %s", last_error
            )
        return ""

    def _generate_once(
        self,
        route: ModelRoute,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        provider = route.provider
        model = route.model

        if provider in {"openai", "openrouter"}:
            client = self._get_client_for_provider(provider)
            request_prompt = prompt
            if provider == "openrouter":
                request_prompt = (
                    prompt
                    + "\n\nPlease format any JSON output in markdown code blocks with ```json```"
                )
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": request_prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = (response.choices[0].message.content or "").strip()
            if provider == "openrouter" and "```json" not in content and "{" in content:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    content = f"```json\n{json_match.group()}\n```"
            self._log_usage(provider, model, prompt, content)
            return content

        if provider == "claude":
            client = self._get_client_for_provider(provider)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            text_content = response.content[0].text.strip()
            self._log_usage(provider, model, prompt, text_content)
            return text_content

        if provider == "google_ai_studio":
            client = self._get_client_for_provider(provider)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=google_genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    thinking_config=google_genai_types.ThinkingConfig(
                        thinking_budget=0,
                    ),
                ),
            )
            text_response = (response.text or "").strip()
            self._log_usage(provider, model, prompt, text_response)
            return text_response

        if provider == "deepseek":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            self._log_usage(provider, model, prompt, content)
            return content

        if provider == "mistral":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.mistral_api_key}",
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            self._log_usage(provider, model, prompt, content)
            return content

        raise ValueError(f"Unsupported LLM provider: {provider}")

    def generate_content(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        language: str = "English",
    ) -> str:
        return self._request_with_fallback(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            language=language,
            require_valid_json=False,
        )

    def generate_content_with_json_repair(
        self, original_prompt: str, max_tokens: int = 2000, temperature: float = 0.7
    ) -> str:
        return self._request_with_fallback(
            prompt=original_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            require_valid_json=True,
        )
