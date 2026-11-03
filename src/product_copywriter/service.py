"""Application service and deterministic hallucination guard."""

import json
import re
from typing import Protocol

from .errors import GroundingError
from .models import Characteristic, GeneratedCopy, ProductCard, ProductInput

_DASH_TRANSLATION = str.maketrans({char: "-" for char in "‐‑‒–—−"})
_DIGIT_TOKEN = re.compile(r"[\w%+./°-]*\d[\w%+./°-]*", flags=re.UNICODE)


class CopyProvider(Protocol):
    """Boundary implemented by an LLM provider."""

    def generate(self, product: ProductInput) -> GeneratedCopy:
        """Generate editorial fields for one product."""


class ProductCardService:
    """Compose an LLM draft with source-controlled technical fields."""

    def __init__(self, provider: CopyProvider) -> None:
        self._provider = provider

    def generate(self, product: ProductInput) -> ProductCard:
        generated = self._provider.generate(product)
        validate_grounding(product, generated)

        characteristics = [
            Characteristic(name=name, value=value) for name, value in product.specs.items()
        ]
        if not characteristics:
            characteristics = [
                Characteristic(name="Ключевые характеристики", value="данных нет")
            ]

        missing_fields = [
            field
            for field, missing in (
                ("manufacturer", not product.manufacturer),
                ("specs", not product.specs),
                ("description", not product.description),
            )
            if missing
        ]

        return ProductCard(
            product_name=product.name,
            manufacturer=product.manufacturer or "данных нет",
            characteristics=characteristics,
            missing_fields=missing_fields,
            source_url=product.source_url,
            **generated.model_dump(),
        )


def validate_grounding(product: ProductInput, generated: GeneratedCopy) -> None:
    """Reject digit-bearing values that cannot be traced to source fields."""

    source_payload = product.model_dump(mode="json", exclude={"source_url"})
    source_text = json.dumps(source_payload, ensure_ascii=False)
    generated_text = json.dumps(generated.model_dump(mode="json"), ensure_ascii=False)

    source_tokens = set(_extract_digit_tokens(source_text))
    for token in _extract_digit_tokens(generated_text):
        if _is_grounded_token(token, source_tokens):
            continue
        raise GroundingError(
            "Результат отклонён: значение "
            f"«{token}» не найдено во входных данных. Повторите генерацию или уточните вход."
        )


def _extract_digit_tokens(text: str) -> list[str]:
    normalized = text.translate(_DASH_TRANSLATION).casefold()
    return [match.group(0).strip(".-/") for match in _DIGIT_TOKEN.finditer(normalized)]


def _is_grounded_token(token: str, source_tokens: set[str]) -> bool:
    if token.startswith("b2b"):
        return True
    if token in source_tokens:
        return True
    if token[-1:].isdigit() and any(character.isalpha() for character in token):
        return any(source_token.startswith(f"{token}-") for source_token in source_tokens)
    return False
