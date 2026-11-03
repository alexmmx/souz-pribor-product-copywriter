import json

from product_copywriter.models import Characteristic, ProductCard
from product_copywriter.renderers import render_json, render_markdown


def make_card() -> ProductCard:
    return ProductCard(
        product_name="ПМ01-24.АВ",
        manufacturer="ОВЕН",
        seo_title="ОВЕН ПМ01-24.АВ - GSM/GPRS-модем",
        seo_description="А" * 800,
        characteristics=[
            Characteristic(name="Интерфейс", value="RS-232/RS-485"),
            Characteristic(name="Питание", value="10-30 В"),
        ],
        search_queries=["ПМ01-24.АВ купить", "GSM-модем ОВЕН", "модем RS-485"],
        commercial_block="Подходит для систем диспетчеризации.",
        missing_fields=["description"],
        source_url="https://www.souz-pribor.ru/product/pm01-24-av/",
    )


def test_render_json_returns_readable_unicode_array():
    rendered = render_json([make_card()])

    parsed = json.loads(rendered)
    assert parsed[0]["product_name"] == "ПМ01-24.АВ"
    assert parsed[0]["characteristics"][0] == {
        "name": "Интерфейс",
        "value": "RS-232/RS-485",
    }
    assert "\\u041e" not in rendered


def test_render_markdown_contains_copy_ready_sections_and_missing_fields():
    rendered = render_markdown([make_card()])

    assert "# Черновики товарных карточек" in rendered
    assert "## ОВЕН ПМ01-24.АВ - GSM/GPRS-модем" in rendered
    assert "### SEO-описание" in rendered
    assert "**Интерфейс:** RS-232/RS-485" in rendered
    assert "### Поисковые запросы" in rendered
    assert "### Commercial-блок" in rendered
    assert "Описание или фрагмент паспорта" in rendered
    assert "https://www.souz-pribor.ru/product/pm01-24-av/" in rendered
