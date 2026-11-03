"""Copy-ready JSON and Markdown renderers."""

import json

from .models import ProductCard

_MISSING_LABELS = {
    "manufacturer": "Производитель",
    "specs": "Ключевые характеристики",
    "description": "Описание или фрагмент паспорта",
}


def render_json(cards: list[ProductCard]) -> str:
    """Render cards as a stable UTF-8 JSON array."""

    payload = [card.model_dump(mode="json") for card in cards]
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_markdown(cards: list[ProductCard]) -> str:
    """Render cards as sections convenient for a content manager to copy."""

    sections = ["# Черновики товарных карточек"]
    for card in cards:
        lines = [
            f"## {card.seo_title}",
            "",
            f"**Исходный товар:** {card.product_name}",
            f"**Производитель:** {card.manufacturer}",
        ]
        if card.source_url is not None:
            lines.append(f"**Источник:** {card.source_url}")
        lines.extend(
            [
                "",
                "### SEO-описание",
                "",
                card.seo_description,
                "",
                "### Ключевые характеристики",
                "",
            ]
        )
        lines.extend(
            f"- **{item.name}:** {item.value}" for item in card.characteristics
        )
        lines.extend(["", "### Поисковые запросы", ""])
        lines.extend(
            f"{index}. {query}" for index, query in enumerate(card.search_queries, start=1)
        )
        lines.extend(
            [
                "",
                "### Commercial-блок",
                "",
                card.commercial_block,
                "",
                "### Требуют уточнения",
                "",
            ]
        )
        if card.missing_fields:
            lines.extend(
                f"- {_MISSING_LABELS.get(field, field)}" for field in card.missing_fields
            )
        else:
            lines.append("Нет.")
        sections.append("\n".join(lines))
    return "\n\n---\n\n".join(sections) + "\n"

