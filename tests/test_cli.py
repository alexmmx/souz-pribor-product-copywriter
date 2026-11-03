import io
import json

from product_copywriter.cli import main
from product_copywriter.errors import ProviderError
from product_copywriter.models import GeneratedCopy


def generated_copy():
    return GeneratedCopy(
        seo_title="Промышленный прибор",
        seo_description="А" * 800,
        search_queries=["прибор купить", "прибор для предприятия", "промышленный прибор"],
        commercial_block="Подходит для промышленного предприятия.",
    )


class StaticProvider:
    def generate(self, product):
        return generated_copy()


class FailOnSecondProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, product):
        self.calls += 1
        if self.calls == 2:
            raise ProviderError("Тестовый сбой провайдера.")
        return generated_copy()


def write_products(tmp_path, value):
    path = tmp_path / "products.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def test_cli_writes_markdown_to_stdout_and_uses_env_model(tmp_path):
    input_path = write_products(tmp_path, {"name": "Прибор"})
    stdout = io.StringIO()
    stderr = io.StringIO()
    factory_calls = []

    def provider_factory(*, model, api_key):
        factory_calls.append((model, api_key))
        return StaticProvider()

    exit_code = main(
        [str(input_path)],
        provider_factory=provider_factory,
        environ={"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "env-model"},
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    assert "# Черновики товарных карточек" in stdout.getvalue()
    assert stderr.getvalue() == ""
    assert factory_calls == [("env-model", "test-key")]


def test_cli_argument_model_overrides_environment(tmp_path):
    input_path = write_products(tmp_path, {"name": "Прибор"})
    captured = []

    def provider_factory(*, model, api_key):
        captured.append(model)
        return StaticProvider()

    exit_code = main(
        [str(input_path), "--model", "argument-model"],
        provider_factory=provider_factory,
        environ={"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "env-model"},
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    assert exit_code == 0
    assert captured == ["argument-model"]


def test_cli_returns_input_error_without_traceback(tmp_path):
    input_path = tmp_path / "broken.json"
    input_path.write_text("not-json", encoding="utf-8")
    stderr = io.StringIO()

    exit_code = main(
        [str(input_path)],
        provider_factory=lambda **kwargs: StaticProvider(),
        environ={"OPENAI_API_KEY": "test-key"},
        stdout=io.StringIO(),
        stderr=stderr,
    )

    assert exit_code == 2
    assert "Некорректный JSON" in stderr.getvalue()
    assert "Traceback" not in stderr.getvalue()


def test_cli_returns_configuration_error_when_key_is_missing(tmp_path):
    input_path = write_products(tmp_path, {"name": "Прибор"})
    stderr = io.StringIO()

    exit_code = main(
        [str(input_path)],
        provider_factory=lambda **kwargs: StaticProvider(),
        environ={},
        stdout=io.StringIO(),
        stderr=stderr,
    )

    assert exit_code == 3
    assert "OPENAI_API_KEY" in stderr.getvalue()


def test_cli_returns_provider_error_without_traceback(tmp_path):
    input_path = write_products(tmp_path, {"name": "Прибор"})
    stderr = io.StringIO()

    class FailingProvider:
        def generate(self, product):
            raise ProviderError("API временно недоступен.")

    exit_code = main(
        [str(input_path)],
        provider_factory=lambda **kwargs: FailingProvider(),
        environ={"OPENAI_API_KEY": "test-key"},
        stdout=io.StringIO(),
        stderr=stderr,
    )

    assert exit_code == 4
    assert stderr.getvalue().strip() == "Ошибка: API временно недоступен."


def test_cli_does_not_partially_replace_output_when_later_product_fails(tmp_path):
    input_path = write_products(tmp_path, [{"name": "Первый"}, {"name": "Второй"}])
    output_path = tmp_path / "result.md"
    output_path.write_text("Существующий результат", encoding="utf-8")

    exit_code = main(
        [str(input_path), "--output", str(output_path)],
        provider_factory=lambda **kwargs: FailOnSecondProvider(),
        environ={"OPENAI_API_KEY": "test-key"},
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    assert exit_code == 4
    assert output_path.read_text(encoding="utf-8") == "Существующий результат"


def test_cli_atomically_writes_requested_json_output(tmp_path):
    input_path = write_products(tmp_path, {"name": "Прибор"})
    output_path = tmp_path / "nested" / "result.json"

    exit_code = main(
        [str(input_path), "--format", "json", "--output", str(output_path)],
        provider_factory=lambda **kwargs: StaticProvider(),
        environ={"OPENAI_API_KEY": "test-key"},
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    assert exit_code == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))[0]["product_name"] == "Прибор"
