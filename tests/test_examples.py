import json
from pathlib import Path

from product_copywriter.input_loader import load_products
from product_copywriter.models import GeneratedCopy, ProductCard
from product_copywriter.service import validate_grounding

EXAMPLES_ROOT = Path(__file__).parents[1] / "examples"
EDITORIAL_FIELDS = {
    "seo_title",
    "seo_description",
    "search_queries",
    "commercial_block",
}


def test_committed_live_examples_match_inputs_and_grounding_contract():
    products = load_products(EXAMPLES_ROOT / "input" / "products.json")
    payload = json.loads(
        (EXAMPLES_ROOT / "output" / "products.json").read_text(encoding="utf-8")
    )
    cards = [ProductCard.model_validate(item) for item in payload]
    markdown = (EXAMPLES_ROOT / "output" / "products.md").read_text(encoding="utf-8")

    assert len(products) == len(cards) == 2

    for product, card in zip(products, cards, strict=True):
        generated = GeneratedCopy.model_validate(card.model_dump(include=EDITORIAL_FIELDS))

        validate_grounding(product, generated)
        assert [(item.name, item.value) for item in card.characteristics] == list(
            product.specs.items()
        )
        assert card.missing_fields == []
        assert card.seo_title in markdown
        assert card.seo_description in markdown
