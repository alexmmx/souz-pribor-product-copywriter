"""Validated input and output contracts."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints

TrimmedText = Annotated[str, StringConstraints(strip_whitespace=True)]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SeoTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=70)]
SeoDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=800, max_length=1200),
]


class StrictModel(BaseModel):
    """Forbid silent input/output shape changes."""

    model_config = ConfigDict(extra="forbid")


class ProductInput(StrictModel):
    """Source facts for one product."""

    name: NonEmptyText
    manufacturer: TrimmedText = ""
    specs: dict[NonEmptyText, NonEmptyText] = Field(default_factory=dict)
    description: TrimmedText = ""
    source_url: HttpUrl | None = None


class GeneratedCopy(StrictModel):
    """Editorial fields produced by the language model."""

    seo_title: SeoTitle
    seo_description: SeoDescription
    search_queries: list[NonEmptyText] = Field(min_length=3, max_length=5)
    commercial_block: NonEmptyText


class Characteristic(StrictModel):
    """A technical characteristic copied from source input."""

    name: NonEmptyText
    value: NonEmptyText


class ProductCard(GeneratedCopy):
    """Complete, user-facing product-card draft."""

    product_name: NonEmptyText
    manufacturer: TrimmedText
    characteristics: list[Characteristic] = Field(min_length=1)
    missing_fields: list[str] = Field(default_factory=list)
    source_url: HttpUrl | None = None

