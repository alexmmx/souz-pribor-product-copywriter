import json

from product_copywriter.models import ProductInput
from product_copywriter.prompts import SYSTEM_PROMPT, build_input_message


def test_system_prompt_requires_source_only_facts_and_missing_markers():
    prompt = SYSTEM_PROMPT.lower()

    assert "только" in prompt and "вход" in prompt
    assert "не используй внешние знания" in prompt
    assert "данных нет" in prompt
    assert "цены" in prompt and "гарантии" in prompt
    assert "цифрами" in prompt and "дословно" in prompt


def test_build_input_message_contains_exact_source_json():
    product = ProductInput(
        name="МК110-224.8Д.4Р [М01]",
        manufacturer="ОВЕН",
        specs={"Интерфейс": "RS-485", "Питание": "90...264 В"},
        description="Комбинированный модуль ввода-вывода.",
        source_url="https://www.souz-pribor.ru/product/mk110-8d-4r/",
    )
    expected_json = json.dumps(
        product.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    message = build_input_message(product)

    assert expected_json in message
    lowered = message.lower()
    assert "единственн" in lowered and "источник" in lowered and "фактов" in lowered
