import json

import pytest

from product_copywriter.errors import InputValidationError
from product_copywriter.input_loader import load_products


def write_json(tmp_path, value):
    path = tmp_path / "products.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_products_accepts_one_object(tmp_path):
    path = write_json(
        tmp_path,
        {
            "name": "ПМ01-24.АВ",
            "manufacturer": "ОВЕН",
            "specs": {"Питание": "10-30 В"},
            "description": "GSM/GPRS-модем",
        },
    )

    products = load_products(path)

    assert len(products) == 1
    assert products[0].name == "ПМ01-24.АВ"
    assert products[0].specs == {"Питание": "10-30 В"}


def test_load_products_accepts_a_list_and_defaults_optional_fields(tmp_path):
    path = write_json(tmp_path, [{"name": "Первый"}, {"name": "Второй"}])

    products = load_products(path)

    assert [product.name for product in products] == ["Первый", "Второй"]
    assert products[0].manufacturer == ""
    assert products[0].specs == {}
    assert products[0].description == ""


def test_load_products_rejects_malformed_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"name":', encoding="utf-8")

    with pytest.raises(InputValidationError, match="Некорректный JSON"):
        load_products(path)


@pytest.mark.parametrize("value", [42, "товар", True, None])
def test_load_products_rejects_top_level_scalar(tmp_path, value):
    path = write_json(tmp_path, value)

    with pytest.raises(InputValidationError, match="объектом или массивом"):
        load_products(path)


def test_load_products_reports_object_field_path_for_blank_name(tmp_path):
    path = write_json(tmp_path, {"name": "   "})

    with pytest.raises(InputValidationError, match=r"name:.*пуст"):
        load_products(path)


def test_load_products_reports_batch_item_path_for_blank_name(tmp_path):
    path = write_json(tmp_path, [{"name": "Исправен"}, {"name": "\t"}])

    with pytest.raises(InputValidationError, match=r"\[1\]\.name:.*пуст"):
        load_products(path)


def test_load_products_rejects_an_empty_list(tmp_path):
    path = write_json(tmp_path, [])

    with pytest.raises(InputValidationError, match="не содержит товаров"):
        load_products(path)
