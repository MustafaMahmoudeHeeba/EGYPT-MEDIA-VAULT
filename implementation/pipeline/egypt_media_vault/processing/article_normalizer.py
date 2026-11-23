import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pipeline.egypt_media_vault.domain.raw_article import RawArticle
from pipeline.egypt_media_vault.domain.article import Article


class ArticleNormalizer:
    """
    Converts validated RawArticle objects into normalized Article objects.

    Responsibilities:
        - Normalize text fields.
        - Normalize article URLs.
        - Standardize categories.
        - Standardize timestamps to UTC.
        - Preserve original source date values.
        - Preserve article image URLs.
        - Set ingestion metadata.

    Hashing, deduplication, and story clustering are handled separately.
    """

    TRACKING_PARAMETERS = {
        "fbclid",
        "gclid",
        "dclid",
        "msclkid",
        "ref",
        "ref_src",
    }

    # Map known category variations to one canonical category.
    CATEGORY_ALIASES = {
        "عرب و عالم": "عرب وعالم",
        "عرب والعالم": "عرب وعالم",

        "الفن": "فن",
        "الفنون": "فن",

        "التكنولوجيا": "تكنولوجيا",

        "الصحة": "صحة",

        "المرأة والمنوعات": "مرأة ومنوعات",
        "مرأة و منوعات": "مرأة ومنوعات",
    }

    def normalize(self, raw_article: RawArticle) -> Article:
        """
        Convert a RawArticle into a normalized Article.
        """

        title = self._normalize_text(raw_article.title)
        source = self._normalize_source(raw_article.source)

        if not title:
            raise ValueError(
                "Cannot normalize an article with an empty title."
            )

        if not source:
            raise ValueError(
                "Cannot normalize an article with an empty source."
            )

        if not self._is_valid_url(raw_article.url):
            raise ValueError(
                "Cannot normalize an article with an invalid URL."
            )

        # Publication date is optional.
        publication_date = self._normalize_datetime(
            raw_article.publication_date
        )

        return Article(
            title=title,
            source=source,
            url=self._normalize_url(raw_article.url),
            publication_date=publication_date,

            # Preserve original date text from the source.
            raw_publication_text=raw_article.raw_publication_text,
            raw_update_text=raw_article.raw_update_text,

            updated_at=self._normalize_datetime(raw_article.updated_at),
            category=self._normalize_category(raw_article.category),
            author=self._normalize_text(raw_article.author),
            description=self._normalize_text(raw_article.description),
            content=self._normalize_content(raw_article.content),

            # Preserve and normalize the article image URL.
            image_url=self._normalize_image_url(
                raw_article.image_url
            ),

            ingestion_date=datetime.now(timezone.utc),
            scraped_at=self._normalize_datetime(raw_article.scraped_at),
        )

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        """
        Remove extra whitespace from a text value.
        """

        if value is None:
            return None

        normalized = re.sub(r"\s+", " ", value).strip()

        return normalized or None

    @classmethod
    def _normalize_category(cls, value: str | None) -> str | None:
        """
        Standardize known category variations.

        Unknown categories are preserved after whitespace normalization.
        """

        normalized = cls._normalize_text(value)

        if normalized is None:
            return None

        lookup_key = normalized.casefold()

        return cls.CATEGORY_ALIASES.get(
            lookup_key,
            normalized,
        )

    @staticmethod
    def _normalize_content(value: str | None) -> str | None:
        """
        Clean article content while preserving paragraph boundaries.
        """

        if value is None:
            return None

        paragraphs = [
            re.sub(r"[ \t]+", " ", paragraph).strip()
            for paragraph in value.splitlines()
        ]

        paragraphs = [
            paragraph for paragraph in paragraphs if paragraph
        ]

        return "\n\n".join(paragraphs) or None

    @staticmethod
    def _normalize_source(value: str) -> str:
        """
        Normalize source identifiers to lowercase.
        """

        return value.strip().lower()

    @classmethod
    def _normalize_url(cls, url: str) -> str:
        """
        Remove URL fragments and known tracking parameters.

        Preserve meaningful query parameters because they may be
        required to identify the actual article.
        """

        parsed = urlsplit(url.strip())

        filtered_query = [
            (key, value)
            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
            if not (
                key.lower().startswith("utm_")
                or key.lower() in cls.TRACKING_PARAMETERS
            )
        ]

        normalized_query = urlencode(filtered_query, doseq=True)

        return urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path,
                normalized_query,
                "",
            )
        )

    @staticmethod
    def _normalize_image_url(
        image_url: str | None,
    ) -> str | None:
        """
        Normalize an article image URL.

        Image URLs are stored as URLs, not downloaded image binaries.
        Tracking query parameters and fragments are removed while
        preserving the actual image location.
        """

        if image_url is None:
            return None

        image_url = image_url.strip()

        if not image_url:
            return None

        if not ArticleNormalizer._is_valid_url(image_url):
            return None

        return ArticleNormalizer._normalize_url(image_url)

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """
        Check whether a URL uses HTTP or HTTPS and has a hostname.
        """

        try:
            parsed = urlsplit(url.strip())

            return (
                parsed.scheme in {"http", "https"}
                and bool(parsed.netloc)
                and bool(parsed.hostname)
            )
        except ValueError:
            return False

    @staticmethod
    def _is_timezone_aware(value: datetime | None) -> bool:
        """
        Check whether a datetime contains valid timezone information.
        """

        if value is None:
            return True

        return (
            isinstance(value, datetime)
            and value.tzinfo is not None
            and value.utcoffset() is not None
        )

    @classmethod
    def _normalize_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """
        Convert timezone-aware datetime values to UTC.
        """

        if value is None:
            return None

        if not isinstance(value, datetime):
            raise ValueError(
                "Timestamp values must be datetime objects."
            )

        if not cls._is_timezone_aware(value):
            raise ValueError(
                "Timestamp values must include timezone information."
            )

        return value.astimezone(timezone.utc)