import pytest
from pydantic import ValidationError

from product_copywriter.models import GeneratedCopy, ProductInput


def valid_copy(**overrides):
    values = {
        "seo_title": "ОВЕН ПМ01-24.АВ - GSM/GPRS-модем",
        "seo_description": "А" * 800,
        "search_queries": ["запрос один", "запрос два", "запрос три"],
        "commercial_block": "Для систем диспетчеризации.",
    }
    values.update(overrides)
    return GeneratedCopy(**values)


def test_product_input_strips_text_and_spec_whitespace():
    product = ProductInput(
        name="  ПМ01-24.АВ  ",
        manufacturer="  ОВЕН ",
        specs={" Питание ": " 10-30 В "},
        description="  GSM/GPRS-модем  ",
    )

    assert product.name == "ПМ01-24.АВ"
    assert product.manufacturer == "ОВЕН"
    assert product.specs == {"Питание": "10-30 В"}
    assert product.description == "GSM/GPRS-модем"


def test_generated_copy_accepts_exact_boundaries():
    copy = valid_copy(
        seo_title="Т" * 70,
        seo_description="О" * 1200,
        search_queries=["один", "два", "три", "четыре", "пять"],
    )

    assert len(copy.seo_title) == 70
    assert len(copy.seo_description) == 1200
    assert len(copy.search_queries) == 5


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("seo_title", "Т" * 71),
        ("seo_description", "О" * 799),
        ("seo_description", "О" * 1201),
        ("search_queries", ["один", "два"]),
        ("search_queries", ["1", "2", "3", "4", "5", "6"]),
    ],
)
def test_generated_copy_rejects_out_of_contract_values(field, value):
    with pytest.raises(ValidationError):
        valid_copy(**{field: value})


def test_product_input_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ProductInput(name="ПМ01", unsupported="value")


def test_generated_copy_rejects_duplicate_search_queries_after_normalization():
    with pytest.raises(ValidationError):
        valid_copy(
            search_queries=[
                "Промышленный прибор купить",
                " промышленный ПРИБОР купить ",
                "другой запрос",
            ]
        )
