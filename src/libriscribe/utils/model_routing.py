from dataclasses import dataclass
from typing import Iterable, List, Optional

from libriscribe.settings import Settings

SUPPORTED_PROVIDERS = (
    "openai",
    "claude",
    "google_ai_studio",
    "deepseek",
    "mistral",
    "openrouter",
)


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str

    @property
    def label(self) -> str:
        return f"{self.provider}/{self.model}"


def parse_fallback_chain_string(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def get_default_model_for_provider(
    provider: str, settings: Optional[Settings] = None
) -> str:
    settings = settings or Settings()
    return {
        "openai": settings.openai_model,
        "claude": settings.claude_model,
        "google_ai_studio": settings.google_ai_studio_model,
        "deepseek": settings.deepseek_model,
        "mistral": settings.mistral_model,
        "openrouter": settings.openrouter_model,
    }.get(provider, "")


def normalize_fallback_chain(raw_chain: Optional[Iterable[str]]) -> List[str]:
    if not raw_chain:
        return []

    normalized: List[str] = []
    for item in raw_chain:
        value = str(item).strip()
        if value:
            normalized.append(value)
    return normalized


def parse_route_reference(
    reference: str,
    current_provider: str,
    settings: Optional[Settings] = None,
) -> ModelRoute:
    settings = settings or Settings()
    value = reference.strip()

    if value in SUPPORTED_PROVIDERS:
        return ModelRoute(
            provider=value,
            model=get_default_model_for_provider(value, settings),
        )

    for provider in SUPPORTED_PROVIDERS:
        prefix = f"{provider}/"
        if value.startswith(prefix):
            explicit_model = value[len(prefix) :].strip()
            return ModelRoute(
                provider=provider,
                model=explicit_model
                or get_default_model_for_provider(provider, settings),
            )

    return ModelRoute(provider=current_provider, model=value)


def build_fallback_route_chain(
    primary_provider: str,
    primary_model: str,
    fallback_chain: Optional[Iterable[str]] = None,
    settings: Optional[Settings] = None,
) -> List[ModelRoute]:
    settings = settings or Settings()
    routes = [
        ModelRoute(
            provider=primary_provider,
            model=primary_model
            or get_default_model_for_provider(primary_provider, settings),
        )
    ]

    seen = {(routes[0].provider, routes[0].model)}
    for item in normalize_fallback_chain(fallback_chain):
        route = parse_route_reference(item, primary_provider, settings)
        key = (route.provider, route.model)
        if key not in seen and route.model:
            routes.append(route)
            seen.add(key)

    return routes
