"""Command-line interface for product-card generation."""

import argparse
import os
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TextIO

from dotenv import load_dotenv

from .errors import (
    ConfigurationError,
    GroundingError,
    InputFileError,
    InputValidationError,
    ProviderError,
)
from .input_loader import load_products
from .provider import OpenAIProvider
from .renderers import render_json, render_markdown
from .service import CopyProvider, ProductCardService

DEFAULT_MODEL = "gpt-6.1-sol"
ProviderFactory = Callable[..., CopyProvider]


def main(
    argv: Sequence[str] | None = None,
    *,
    provider_factory: ProviderFactory | None = None,
    environ: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the CLI and return a stable process exit code."""

    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr
    args = _build_parser().parse_args(argv)

    try:
        products = load_products(args.input)
        runtime_environment = environ if environ is not None else _load_environment()
        api_key = runtime_environment.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ConfigurationError(
                "Не задан OPENAI_API_KEY. Добавьте ключ в .env.local или окружение."
            )
        model = args.model or runtime_environment.get("OPENAI_MODEL") or DEFAULT_MODEL

        factory = provider_factory or _default_provider_factory
        service = ProductCardService(factory(model=model, api_key=api_key))
        cards = [service.generate(product) for product in products]
        rendered = render_json(cards) if args.output_format == "json" else render_markdown(cards)

        if args.output is None:
            output_stream.write(rendered)
        else:
            _atomic_write(args.output, rendered)
            output_stream.write(f"Результат сохранён: {args.output}\n")
        return 0
    except (InputFileError, InputValidationError) as exc:
        _print_error(error_stream, exc)
        return 2
    except ConfigurationError as exc:
        _print_error(error_stream, exc)
        return 3
    except ProviderError as exc:
        _print_error(error_stream, exc)
        return 4
    except GroundingError as exc:
        _print_error(error_stream, exc)
        return 5
    except OSError as exc:
        _print_error(error_stream, f"Не удалось записать результат: {exc.filename or 'файл'}")
        return 6


def entrypoint() -> None:
    """Installed console-script entry point."""

    raise SystemExit(main())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="product-copywriter",
        description="Создать проверенный черновик B2B-карточки товара через OpenAI.",
    )
    parser.add_argument("input", type=Path, help="JSON-файл с одним товаром или массивом")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("markdown", "json"),
        default="markdown",
        help="формат результата (по умолчанию: markdown)",
    )
    parser.add_argument("--output", type=Path, help="записать результат в файл")
    parser.add_argument("--model", help=f"модель OpenAI (по умолчанию: {DEFAULT_MODEL})")
    return parser


def _load_environment() -> Mapping[str, str]:
    load_dotenv(".env.local", override=False)
    load_dotenv(".env", override=False)
    return os.environ


def _default_provider_factory(*, model: str, api_key: str) -> CopyProvider:
    return OpenAIProvider(model=model, api_key=api_key)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _print_error(stream: TextIO, error: object) -> None:
    stream.write(f"Ошибка: {error}\n")


if __name__ == "__main__":
    entrypoint()
