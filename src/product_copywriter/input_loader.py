"""Read product input without leaking implementation errors to the CLI."""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .errors import InputFileError, InputValidationError
from .models import ProductInput


def load_products(path: Path) -> list[ProductInput]:
    """Load one product object or a non-empty list of product objects."""

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputFileError(f"Не удалось прочитать входной файл: {path}") from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InputValidationError(
            f"Некорректный JSON: строка {exc.lineno}, столбец {exc.colno}."
        ) from exc

    if isinstance(payload, dict):
        items = [payload]
        prefixes = [""]
    elif isinstance(payload, list):
        if not payload:
            raise InputValidationError("Входной массив не содержит товаров.")
        items = payload
        prefixes = [f"[{index}]." for index in range(len(items))]
    else:
        raise InputValidationError("Верхний уровень JSON должен быть объектом или массивом.")

    products: list[ProductInput] = []
    for item, prefix in zip(items, prefixes, strict=True):
        try:
            products.append(ProductInput.model_validate(item))
        except ValidationError as exc:
            raise InputValidationError(_format_validation_error(exc, prefix)) from exc
    return products


def _format_validation_error(exc: ValidationError, prefix: str) -> str:
    rendered: list[str] = []
    for error in exc.errors():
        location = _format_location(error.get("loc", ()))
        path = f"{prefix}{location}" if location else prefix.rstrip(".")
        kind = error.get("type", "")
        message = _translate_message(kind, error.get("msg", "некорректное значение"))
        rendered.append(f"{path}: {message}" if path else message)
    return "Ошибки входных данных: " + "; ".join(rendered)


def _format_location(location: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for part in location:
        if isinstance(part, int):
            parts.append(f"[{part}]")
        elif parts:
            parts.append(f".{part}")
        else:
            parts.append(str(part))
    return "".join(parts)


def _translate_message(kind: str, fallback: str) -> str:
    if kind == "missing":
        return "обязательное поле отсутствует"
    if kind in {"string_too_short", "string_unicode"}:
        return "поле не может быть пустым"
    if kind == "extra_forbidden":
        return "неизвестное поле"
    if kind in {"dict_type", "model_type"}:
        return "ожидался JSON-объект"
    return fallback
