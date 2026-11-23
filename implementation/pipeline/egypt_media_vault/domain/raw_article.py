from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class RawArticle:
    """
    Represents an article exactly as collected from a news source.

    Original source values are preserved separately from parsed values.
    Validation, normalization, hashing, deduplication, and story
    clustering happen in later processing stages.
    """

    title: str
    source: str
    url: str
    publication_date: Optional[datetime] = None

    # Original date values as provided by the source.
    raw_publication_text: Optional[str] = None
    raw_update_text: Optional[str] = None

    # Optional article metadata.
    updated_at: Optional[datetime] = None
    category: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None

    # Article media.
    # Stores the original image URL collected from the source.
    image_url: Optional[str] = None

    # Collection metadata.
    scraped_at: Optional[datetime] = None

    # Preserve the original HTML exactly as received.
    raw_html: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize empty optional strings except raw HTML."""

        optional_string_fields = (
            "raw_publication_text",
            "raw_update_text",
            "category",
            "author",
            "description",
            "content",
            "image_url",
        )

        for field_name in optional_string_fields:
            value = getattr(self, field_name)

            if isinstance(value, str):
                normalized_value = value.strip()
                setattr(
                    self,
                    field_name,
                    normalized_value or None,
                )