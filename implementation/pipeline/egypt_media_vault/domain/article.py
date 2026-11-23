from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Article:
    """
    Represents a validated and normalized news article.

    Unlike RawArticle, this model represents an article after
    validation and normalization. It is the main domain object
    passed to hashing, deduplication, story matching, and storage.

    Publication timestamps are optional because an article
    can remain valid even when its publication date is unavailable.
    """

    title: str
    source: str
    url: str
    publication_date: Optional[datetime] = None

    # Original date values provided by the source.
    raw_publication_text: Optional[str] = None
    raw_update_text: Optional[str] = None

    updated_at: Optional[datetime] = None
    category: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None

    # Article media.
    image_url: Optional[str] = None

    # Canonical URL and generated identifiers/hashes.
    canonical_url: Optional[str] = None
    canonical_url_hash: Optional[str] = None

    # Stable article identifier.
    # Generated from the canonical URL hash.
    article_id: Optional[str] = None

    # Hash of normalized article title.
    title_hash: Optional[str] = None

    # Hash of normalized article content.
    content_fingerprint: Optional[str] = None

    # Story clustering identifier.
    story_cluster_id: Optional[str] = None

    # Persisted story identifier.
    # Generated during story clustering and persisted to SQL staging.
    story_id: Optional[str] = None

    ingestion_date: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Normalize string values after object creation."""

        self.title = self.title.strip()
        self.source = self.source.strip()
        self.url = self.url.strip()

        optional_string_fields = (
            "raw_publication_text",
            "raw_update_text",
            "category",
            "author",
            "description",
            "content",
            "image_url",
            "canonical_url",
            "canonical_url_hash",
            "article_id",
            "title_hash",
            "content_fingerprint",
            "story_cluster_id",
            "story_id",
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

        if not self.title:
            raise ValueError("Article title cannot be empty.")

        if not self.source:
            raise ValueError("Article source cannot be empty.")

        if not self.url:
            raise ValueError("Article URL cannot be empty.")

    @property
    def effective_canonical_url(self) -> str:
        """
        Return the canonical URL when available,
        otherwise fall back to the original article URL.
        """
        return self.canonical_url or self.url

    @property
    def has_story_cluster(self) -> bool:
        """Return True when the article belongs to a story cluster."""
        return bool(self.story_cluster_id)

    @property
    def has_story_id(self) -> bool:
        """Return True when a persisted story ID is available."""
        return bool(self.story_id)

    @property
    def has_content_fingerprint(self) -> bool:
        """Return True when content fingerprinting has been completed."""
        return bool(self.content_fingerprint)

    @property
    def has_article_id(self) -> bool:
        """Return True when a stable article ID has been generated."""
        return bool(self.article_id)

    @property
    def has_title_hash(self) -> bool:
        """Return True when a title hash has been generated."""
        return bool(self.title_hash)