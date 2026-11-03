"""OpenAI Responses API adapter."""

from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from pydantic import ValidationError

from .errors import ConfigurationError, ProviderError
from .models import GeneratedCopy, ProductInput
from .prompts import SYSTEM_PROMPT, build_input_message


class OpenAIProvider:
    """Generate validated editorial fields through OpenAI Responses."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._model = model.strip()
        if not self._model:
            raise ConfigurationError("Не указана модель OpenAI.")

        if client is None:
            if not api_key:
                raise ConfigurationError(
                    "Не задан OPENAI_API_KEY. Добавьте ключ в .env.local или окружение."
                )
            client = OpenAI(api_key=api_key, timeout=60.0, max_retries=2)
        self._client = client

    def generate(self, product: ProductInput) -> GeneratedCopy:
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=SYSTEM_PROMPT,
                input=build_input_message(product),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "product_card_copy",
                        "description": "Редакционные поля черновика B2B-карточки товара",
                        "strict": True,
                        "schema": GeneratedCopy.model_json_schema(),
                    }
                },
                store=False,
            )
        except AuthenticationError as exc:
            raise ProviderError("OpenAI отклонил API-ключ. Проверьте OPENAI_API_KEY.") from exc
        except APITimeoutError as exc:
            raise ProviderError(
                "Превышено время ожидания OpenAI API. Повторите запрос позже."
            ) from exc
        except RateLimitError as exc:
            raise ProviderError(
                "OpenAI API вернул лимит запросов или квоты. Проверьте баланс и повторите позже."
            ) from exc
        except APIConnectionError as exc:
            raise ProviderError("Не удалось подключиться к OpenAI API.") from exc
        except APIStatusError as exc:
            raise ProviderError(
                f"OpenAI API завершил запрос с ошибкой HTTP {exc.status_code}."
            ) from exc
        except OpenAIError as exc:
            raise ProviderError("OpenAI API не смог обработать запрос.") from exc

        if _has_refusal(response):
            raise ProviderError(
                "Модель отказалась сформировать карточку. Проверьте входные данные."
            )

        output_text = getattr(response, "output_text", "")
        if not isinstance(output_text, str) or not output_text.strip():
            raise ProviderError("OpenAI API вернул пустой ответ.")

        try:
            return GeneratedCopy.model_validate_json(output_text)
        except ValidationError as exc:
            raise ProviderError(
                "Ответ OpenAI не соответствует ожидаемой структуре карточки."
            ) from exc


def _has_refusal(response: Any) -> bool:
    for item in getattr(response, "output", None) or []:
        content = (
            item.get("content", [])
            if isinstance(item, dict)
            else getattr(item, "content", [])
        )
        for part in content or []:
            part_type = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
            if part_type == "refusal":
                return True
    return False
