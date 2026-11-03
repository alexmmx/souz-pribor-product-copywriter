from dataclasses import dataclass

import pytest

from product_copywriter.errors import GroundingError
from product_copywriter.models import GeneratedCopy, ProductInput
from product_copywriter.service import ProductCardService, validate_grounding


def make_description(*facts: str) -> str:
    prefix = " ".join(facts)
    filler = " Решение предназначено для промышленной автоматизации и диспетчеризации."
    text = prefix
    while len(text) < 820:
        text += filler
    return text[:900]


def make_copy(**overrides) -> GeneratedCopy:
    values = {
        "seo_title": "Модуль для промышленной автоматизации",
        "seo_description": make_description(),
        "search_queries": [
            "модуль промышленной автоматизации",
            "модуль для диспетчеризации",
            "оборудование автоматизации",
        ],
        "commercial_block": "Подходит для систем автоматизации и диспетчеризации.",
    }
    values.update(overrides)
    return GeneratedCopy(**values)


@dataclass
class StaticProvider:
    copy: GeneratedCopy

    def generate(self, product: ProductInput) -> GeneratedCopy:
        return self.copy


def test_service_copies_characteristics_from_input_instead_of_model():
    product = ProductInput(
        name="Модуль ввода-вывода",
        manufacturer="ОВЕН",
        specs={"Интерфейс": "RS-485", "Питание": "90...264 В"},
        description="Модуль для систем автоматизации.",
    )

    card = ProductCardService(StaticProvider(make_copy())).generate(product)

    assert [item.model_dump() for item in card.characteristics] == [
        {"name": "Интерфейс", "value": "RS-485"},
        {"name": "Питание", "value": "90...264 В"},
    ]
    assert card.missing_fields == []


def test_service_marks_absent_optional_fields_and_uses_visible_placeholders():
    product = ProductInput(name="Прибор")

    card = ProductCardService(StaticProvider(make_copy())).generate(product)

    assert card.manufacturer == "данных нет"
    assert card.missing_fields == ["manufacturer", "specs", "description"]
    assert [item.model_dump() for item in card.characteristics] == [
        {"name": "Ключевые характеристики", "value": "данных нет"}
    ]


def test_grounding_accepts_digit_values_copied_from_source():
    product = ProductInput(
        name="МК110-224.8Д.4Р [М01]",
        manufacturer="ОВЕН",
        specs={
            "Интерфейс": "RS-485",
            "Питание": "90...264 В",
            "Входы": "8 каналов",
        },
        description="В сеть могут быть включены до 32 устройств.",
    )
    copy = make_copy(
        seo_title="ОВЕН МК110-224.8Д.4Р [М01] - модуль RS-485",
        seo_description=make_description("90...264 В, RS-485, 8 каналов и до 32 устройств."),
        search_queries=[
            "купить МК110-224.8Д.4Р",
            "модуль RS-485 ОВЕН",
            "МК110 8 каналов",
        ],
    )

    validate_grounding(product, copy)


def test_grounding_normalizes_unicode_hyphen_variants():
    product = ProductInput(
        name="ПМ01-24.АВ",
        specs={"Интерфейс": "RS-485"},
        description="Модем для удаленного обмена данными.",
    )
    copy = make_copy(
        seo_title="ПМ01‑24.АВ - модем RS‑485",
        seo_description=make_description("ПМ01‑24.АВ и RS‑485."),
        search_queries=["ПМ01‑24.АВ", "модем RS‑485", "модем для диспетчеризации"],
    )

    validate_grounding(product, copy)


def test_grounding_rejects_new_numeric_technical_value():
    product = ProductInput(
        name="Модуль",
        specs={"Входы": "8 каналов"},
        description="Модуль дискретного ввода.",
    )
    copy = make_copy(
        seo_description=make_description("Модуль поддерживает 16 каналов."),
    )

    with pytest.raises(GroundingError, match="16"):
        validate_grounding(product, copy)


def test_grounding_allows_generic_b2b_marker():
    product = ProductInput(name="Прибор", description="Промышленный прибор.")
    copy = make_copy(
        seo_description=make_description("Карточка подходит для B2B-каталога."),
    )

    validate_grounding(product, copy)
