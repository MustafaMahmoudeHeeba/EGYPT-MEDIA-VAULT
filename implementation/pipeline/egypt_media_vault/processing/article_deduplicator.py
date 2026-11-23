import hashlib
import re
import unicodedata

from collections.abc import Iterable

from urllib.parse import urlsplit, urlunsplit

from pipeline.egypt_media_vault.domain.article import Article


class ArticleDeduplicator:
    """
    Detects duplicate articles within the same collection batch.

    Articles from different sources are always preserved,
    even when they contain identical content.

    Responsibilities:
        - Generate canonical URL hashes.
        - Generate stable article IDs.
        - Generate title hashes.
        - Generate content fingerprints.
        - Detect exact duplicates within the same source and batch.
        - Preserve articles with changed content for further processing.
        - Preserve cross-source syndicated articles.

    Persistent duplicate detection and New/Duplicate/Updated
    classification are handled by the Staging Repository.
    """

    def deduplicate(
        self,
        articles: Iterable[Article],
    ) -> tuple[list[Article], list[Article]]:
        """
        Detect duplicates within the current batch.

        Returns:
            unique_articles:
                Articles retained for downstream processing.

            duplicate_articles:
                Exact duplicate articles within the current batch.

        duplicate_matches:
            Maps each duplicate Article identity to its
            matching unique Article.

        Articles with the same canonical URL but different content
        are retained because they may represent updated versions.
        """

        unique_articles: list[Article] = []
        duplicate_articles: list[Article] = []

        self.duplicate_matches: dict[int, Article] = {}

        seen_url_fingerprints: dict[
            tuple[str, str],
            dict[str | None, Article],
        ] = {}

        seen_content_fingerprints: dict[
            tuple[str, str],
            Article,
        ] = {}

        for article in articles:
            self.generate_hashes(article)

            source = self._normalize_source(article.source)

            url_key = (
                source,
                article.canonical_url_hash,
            )

            content_key = (
                source,
                article.content_fingerprint,
            )

            seen_versions = seen_url_fingerprints.get(
                url_key,
                {},
            )

            # Same source + same URL + same content:
            # exact duplicate.
            if article.content_fingerprint in seen_versions:
                duplicate_articles.append(article)

                self.duplicate_matches[id(article)] = (
                    seen_versions[article.content_fingerprint]
                )

                continue

            # Same source + same content under another URL:
            # duplicate content.
            #
            # For an already-seen URL with changed content,
            # preserve the article as a potential update.
            if (
                url_key not in seen_url_fingerprints
                and article.content_fingerprint is not None
                and content_key in seen_content_fingerprints
            ):
                duplicate_articles.append(article)

                self.duplicate_matches[id(article)] = (
                    seen_content_fingerprints[content_key]
                )

                continue

            unique_articles.append(article)

            seen_url_fingerprints.setdefault(
                url_key,
                {},
            )[article.content_fingerprint] = article

            if article.content_fingerprint is not None:
                seen_content_fingerprints[
                    content_key
                ] = article

        return unique_articles, duplicate_articles

    def generate_hashes(self, article: Article) -> None:
        """
        Generate and assign:

            - canonical URL
            - canonical URL hash
            - stable article ID
            - title hash
            - content fingerprint
        """

        # -------------------------------------------------
        # Canonical URL
        # -------------------------------------------------

        canonical_url = self._normalize_url(
            article.effective_canonical_url
        )

        article.canonical_url = canonical_url

        # -------------------------------------------------
        # Canonical URL hash
        # -------------------------------------------------

        article.canonical_url_hash = self._generate_sha256(
            canonical_url
        )

        # -------------------------------------------------
        # Stable Article ID
        #
        # The article ID is derived from the canonical URL.
        #
        # This means:
        # same canonical URL -> same article_id
        # different canonical URL -> different article_id
        # -------------------------------------------------

        article.article_id = (
            f"article_{article.canonical_url_hash}"
        )

        # -------------------------------------------------
        # Title hash
        # -------------------------------------------------

        normalized_title = self._normalize_title(
            article.title
        )

        if normalized_title:
            article.title_hash = self._generate_sha256(
                normalized_title
            )
        else:
            article.title_hash = None

        # -------------------------------------------------
        # Content fingerprint
        # -------------------------------------------------

        normalized_content = self._normalize_content(
            article.content
        )

        if normalized_content:
            article.content_fingerprint = (
                self._generate_sha256(
                    normalized_content
                )
            )
        else:
            article.content_fingerprint = None

    @staticmethod
    def _normalize_source(source: str) -> str:
        return source.strip().lower()

    @staticmethod
    def _normalize_url(url: str) -> str:
        """
        Normalize URL components before hashing.

        Scheme and hostname are case-insensitive.
        Path and query values are preserved because their case
        may be meaningful to the source website.
        """

        parsed = urlsplit(url.strip())

        normalized_path = parsed.path.rstrip("/")

        return urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                normalized_path,
                parsed.query,
                "",
            )
        )

    @staticmethod
    def _normalize_title(title: str | None) -> str | None:
        """
        Normalize article title before hashing.

        Unicode normalization and whitespace normalization
        make equivalent titles produce the same hash.
        """

        if not title:
            return None

        normalized = unicodedata.normalize(
            "NFKC",
            title,
        )

        normalized = normalized.casefold()

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized or None

    @staticmethod
    def _normalize_content(
        content: str | None,
    ) -> str | None:
        """
        Normalize content for fingerprint comparison.

        Unicode normalization and whitespace normalization
        make equivalent content produce the same fingerprint.
        """

        if not content:
            return None

        normalized = unicodedata.normalize(
            "NFKC",
            content,
        )

        normalized = normalized.casefold()

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized or None

    @staticmethod
    def _generate_sha256(value: str) -> str:
        """
        Generate a SHA-256 hexadecimal digest.
        """

        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()