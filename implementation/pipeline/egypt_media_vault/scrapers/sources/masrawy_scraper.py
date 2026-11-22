import json
import re
import time
import unicodedata

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from pipeline.egypt_media_vault.domain.raw_article import RawArticle
from pipeline.egypt_media_vault.scrapers.base_scraper import BaseScraper
from pipeline.egypt_media_vault.scrapers.http_client import HttpClient


class MasrawyScraper(BaseScraper):
    """
    Scraper for Masrawy news articles and video content.

    Supported content:
    - Regular news articles.
    - Masrawy TV videos.

    Extraction strategy:
    - JSON-LD metadata when available.
    - Open Graph metadata as fallback.
    - Twitter image metadata as fallback.
    - HTML article image extraction as fallback.
    - HTML article content extraction.
    - Related-news filtering.
    """

    BASE_URL = "https://www.masrawy.com"
    HOMEPAGE_URL = "https://www.masrawy.com/"

    MAX_ARTICLES = 5

    ARTICLE_URL_PATTERN = re.compile(
        r"^/news/[^/]+/details/\d{4}/\d{1,2}/\d{1,2}/\d+(?:/.*)?$",
        re.IGNORECASE,
    )

    VIDEO_URL_PATTERN = re.compile(
        r"^/video/.*",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        super().__init__("masrawy")

        self.http_client = HttpClient()

    # =========================================================
    # HTTP
    # =========================================================

    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a webpage.

        HttpClient in this project normally returns HTML as str.
        Response-like objects are also supported.
        """

        try:
            response = self.http_client.get(url)

            if isinstance(response, str):
                return response

            if response is None:
                return None

            if hasattr(response, "text"):
                return response.text

            return None

        except Exception as exc:
            print(f"Failed to fetch {url}: {exc}")
            return None

    # =========================================================
    # URL EXTRACTION
    # =========================================================

    def _is_valid_article_url(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.netloc.lower() not in {
            "www.masrawy.com",
            "masrawy.com",
        }:
            return False

        return bool(self.ARTICLE_URL_PATTERN.match(parsed.path))

    def _is_valid_video_url(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.netloc.lower() not in {
            "www.masrawy.com",
            "masrawy.com",
        }:
            return False

        return bool(self.VIDEO_URL_PATTERN.match(parsed.path))

    def _extract_article_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")

        article_urls = []
        seen_urls = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()

            if not href:
                continue

            full_url = urljoin(self.BASE_URL, href)

            parsed = urlparse(full_url)

            normalized_url = (
                f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            )

            is_valid = (
                self._is_valid_article_url(normalized_url)
                or self._is_valid_video_url(normalized_url)
            )

            if not is_valid:
                continue

            if normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)
            article_urls.append(normalized_url)

        return article_urls

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_text(text: Optional[str]) -> str:
        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)

        text = text.replace("\xa0", " ")
        text = text.replace("\u200f", "")
        text = text.replace("\u200e", "")
        text = text.replace("\u202a", "")
        text = text.replace("\u202b", "")
        text = text.replace("\u202c", "")

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def _normalize_arabic_heading(text: str) -> str:
        """
        Normalize Arabic text for reliable heading comparison.

        Handles:
        - Alef variations.
        - Hamza variations.
        - Arabic diacritics.
        - Tatweel.
        """

        text = unicodedata.normalize("NFKC", text)

        normalized = []

        for char in text:
            if char == "\u0640":
                continue

            if unicodedata.category(char) == "Mn":
                continue

            if char in "أإآٱ":
                char = "ا"

            if char == "ى":
                char = "ي"

            if char == "ؤ":
                char = "و"

            if char == "ئ":
                char = "ي"

            normalized.append(char)

        text = "".join(normalized)
        text = text.casefold()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # =========================================================
    # RELATED CONTENT FILTERING
    # =========================================================

    def _is_related_content_heading(self, text: str) -> bool:
        """
        Detect the beginning of related-news sections.

        Examples:
        - اقرأ أيضًا:
        - اقرأ أيضًأ:
        - اقرأ ايضا
        """

        normalized = self._normalize_arabic_heading(text)

        related_headings = {
            "اقرا ايضا",
            "اقرا ايضا",
            "اقرا ايضاً",
            "اقرا ايضأ",
            "اخبار متعلقه",
            "موضوعات متعلقه",
            "قد يعجبك ايضا",
        }

        if normalized in related_headings:
            return True

        return (
            normalized.startswith("اقرا ايضا")
            or normalized.startswith("اخبار متعلقه")
            or normalized.startswith("موضوعات متعلقه")
        )

    def _is_noise_text(self, text: str) -> bool:
        normalized = self._normalize_arabic_heading(text)

        noise_phrases = {
            "تابعونا",
            "اشترك في النشره الاخباريه",
            "اقرا ايضا",
            "اخبار متعلقه",
            "موضوعات متعلقه",
            "قد يعجبك ايضا",
            "للمزيد من الاخبار",
        }

        if normalized in noise_phrases:
            return True

        return False

    # =========================================================
    # JSON-LD
    # =========================================================

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict[str, Any]:
        """
        Extract NewsArticle or Article JSON-LD.

        Supports:
        - A single JSON object.
        - A list of JSON objects.
        - @graph structures.
        """

        for script in soup.find_all(
            "script",
            type="application/ld+json",
        ):
            raw_json = script.string or script.get_text()

            if not raw_json:
                continue

            try:
                data = json.loads(raw_json.strip())
            except (json.JSONDecodeError, TypeError):
                continue

            result = self._find_article_object(data)

            if result:
                return result

        return {}

    def _find_article_object(self, data: Any) -> dict[str, Any]:
        if isinstance(data, list):
            for item in data:
                result = self._find_article_object(item)

                if result:
                    return result

            return {}

        if not isinstance(data, dict):
            return {}

        article_types = {
            "NewsArticle",
            "Article",
            "ReportageNewsArticle",
            "VideoObject",
        }

        raw_type = data.get("@type", [])

        if isinstance(raw_type, str):
            types = {raw_type}
        elif isinstance(raw_type, list):
            types = set(raw_type)
        else:
            types = set()

        if types.intersection(article_types):
            return data

        graph = data.get("@graph")

        if graph:
            result = self._find_article_object(graph)

            if result:
                return result

        return {}

    # =========================================================
    # META EXTRACTION
    # =========================================================

    @staticmethod
    def _get_meta_content(
        soup: BeautifulSoup,
        *,
        property_name: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[str]:

        if property_name:
            tag = soup.find(
                "meta",
                attrs={"property": property_name},
            )

        elif name:
            tag = soup.find(
                "meta",
                attrs={"name": name},
            )

        else:
            return None

        if not tag:
            return None

        content = tag.get("content")

        return content.strip() if content else None

    def _extract_title(
        self,
        soup: BeautifulSoup,
        json_ld: dict[str, Any],
    ) -> Optional[str]:

        title = (
            json_ld.get("headline")
            or json_ld.get("name")
            or self._get_meta_content(
                soup,
                property_name="og:title",
            )
        )

        if not title:
            title_tag = soup.find("h1")

            if title_tag:
                title = title_tag.get_text(" ", strip=True)

        if not title and soup.title:
            title = soup.title.get_text(" ", strip=True)

        return self._normalize_text(title)

    def _extract_description(
        self,
        soup: BeautifulSoup,
        json_ld: dict[str, Any],
    ) -> Optional[str]:

        description = (
            json_ld.get("description")
            or self._get_meta_content(
                soup,
                property_name="og:description",
            )
            or self._get_meta_content(
                soup,
                name="description",
            )
        )

        return self._normalize_text(description) or None

    def _extract_author(
        self,
        json_ld: dict[str, Any],
        soup: BeautifulSoup,
    ) -> Optional[str]:

        author = json_ld.get("author")

        if isinstance(author, dict):
            author = author.get("name")

        elif isinstance(author, list):
            names = []

            for item in author:
                if isinstance(item, dict):
                    name = item.get("name")

                    if name:
                        names.append(str(name))

                elif isinstance(item, str):
                    names.append(item)

            author = ", ".join(names) if names else None

        if not author:
            author = self._get_meta_content(
                soup,
                name="author",
            )

        return self._normalize_text(author) or None

    # =========================================================
    # IMAGE EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_image_from_json_ld(
        image_data: Any,
    ) -> Optional[str]:
        """
        Extract an image URL from JSON-LD.

        The image field may be:
        - A string.
        - A dictionary containing url/contentUrl.
        - A list of strings/dictionaries.
        """

        if isinstance(image_data, str):
            value = image_data.strip()

            return value or None

        if isinstance(image_data, dict):
            for key in (
                "url",
                "contentUrl",
            ):
                value = image_data.get(key)

                if isinstance(value, str):
                    value = value.strip()

                    if value:
                        return value

        if isinstance(image_data, list):
            for item in image_data:
                result = (
                    MasrawyScraper._extract_image_from_json_ld(
                        item
                    )
                )

                if result:
                    return result

        return None

    @staticmethod
    def _extract_image_src(
        image: Tag,
    ) -> Optional[str]:
        """
        Extract the actual image source from an HTML img element.

        Supports:
        - src
        - data-src
        - data-original
        - data-lazy-src
        - data-image
        - srcset
        """

        attributes = [
            "src",
            "data-src",
            "data-original",
            "data-lazy-src",
            "data-image",
        ]

        for attribute in attributes:
            value = image.get(attribute)

            if isinstance(value, str):
                value = value.strip()

                if value:
                    return value

        # Fallback to srcset.
        srcset = image.get("srcset")

        if isinstance(srcset, str):
            candidates = [
                item.strip()
                for item in srcset.split(",")
                if item.strip()
            ]

            if candidates:
                # Usually the last candidate represents
                # the highest available resolution.
                last_candidate = candidates[-1]

                parts = last_candidate.split()

                if parts:
                    return parts[0].strip()

        return None

    @staticmethod
    def _is_valid_image_url(
        image_url: str,
    ) -> bool:
        """
        Reject obvious invalid image URLs.
        """

        if not image_url:
            return False

        image_url = image_url.strip()

        if not image_url:
            return False

        lowered = image_url.lower()

        if lowered.startswith("data:"):
            return False

        if lowered.startswith("javascript:"):
            return False

        if (
            "placeholder" in lowered
            or "spacer.gif" in lowered
            or "blank.gif" in lowered
        ):
            return False

        return True

    def _extract_image_url(
        self,
        json_ld: dict[str, Any],
        soup: BeautifulSoup,
        article_url: str,
        is_video: bool = False,
    ) -> Optional[str]:
        """
        Extract the article image URL.

        Extraction order:
        1. JSON-LD image.
        2. Open Graph og:image.
        3. Twitter image.
        4. Image inside the article container.
        5. First meaningful image on the article page.

        Returns:
            Absolute image URL or None.
        """

        # ---------------------------------------------------------
        # 1. JSON-LD image
        # ---------------------------------------------------------

        json_ld_image = (
            self._extract_image_from_json_ld(
                json_ld.get("image")
            )
        )

        if (
            json_ld_image
            and self._is_valid_image_url(
                json_ld_image
            )
        ):
            return urljoin(
                article_url,
                json_ld_image,
            )

        # ---------------------------------------------------------
        # 2. Open Graph image
        # ---------------------------------------------------------

        og_image = self._get_meta_content(
            soup,
            property_name="og:image",
        )

        if (
            og_image
            and self._is_valid_image_url(
                og_image
            )
        ):
            return urljoin(
                article_url,
                og_image,
            )

        # ---------------------------------------------------------
        # 3. Twitter image
        # ---------------------------------------------------------

        twitter_image = self._get_meta_content(
            soup,
            name="twitter:image",
        )

        if (
            twitter_image
            and self._is_valid_image_url(
                twitter_image
            )
        ):
            return urljoin(
                article_url,
                twitter_image,
            )

        # ---------------------------------------------------------
        # 4. Image inside article container
        # ---------------------------------------------------------

        container = self._get_content_container(
            soup,
            is_video=is_video,
        )

        if container:
            for image in container.find_all(
                "img"
            ):
                image_url = (
                    self._extract_image_src(
                        image
                    )
                )

                if (
                    image_url
                    and self._is_valid_image_url(
                        image_url
                    )
                ):
                    return urljoin(
                        article_url,
                        image_url,
                    )

        # ---------------------------------------------------------
        # 5. General article-page image fallback
        # ---------------------------------------------------------

        selectors = [
            "article img",
            "[class*='article'] img",
            "[class*='Article'] img",
            "main img",
        ]

        for selector in selectors:
            for image in soup.select(
                selector
            ):
                image_url = (
                    self._extract_image_src(
                        image
                    )
                )

                if (
                    image_url
                    and self._is_valid_image_url(
                        image_url
                    )
                ):
                    return urljoin(
                        article_url,
                        image_url,
                    )

        return None

    # =========================================================
    # DATETIME EXTRACTION
    # =========================================================

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        if not value:
            return None

        if isinstance(value, datetime):
            result = value

        else:
            value = str(value).strip()

            try:
                result = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )

            except ValueError:
                try:
                    result = parsedate_to_datetime(value)

                except (TypeError, ValueError, OverflowError):
                    return None

        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)

        return result

    def _extract_publication_date_text(
        self,
        json_ld: dict[str, Any],
        soup: BeautifulSoup,
    ) -> Optional[str]:
        """
        Extract the original publication date value.

        The fallback order is preserved:
        1. JSON-LD datePublished.
        2. JSON-LD uploadDate.
        3. article:published_time.
        4. og:published_time.
        """

        value = (
            json_ld.get("datePublished")
            or json_ld.get("uploadDate")
            or self._get_meta_content(
                soup,
                property_name="article:published_time",
            )
            or self._get_meta_content(
                soup,
                property_name="og:published_time",
            )
        )

        if value is None:
            return None

        return str(value).strip() or None

    def _extract_updated_at_text(
        self,
        json_ld: dict[str, Any],
        soup: BeautifulSoup,
    ) -> Optional[str]:
        """
        Extract the original update date value.

        The fallback order is preserved:
        1. JSON-LD dateModified.
        2. article:modified_time.
        """

        value = (
            json_ld.get("dateModified")
            or self._get_meta_content(
                soup,
                property_name="article:modified_time",
            )
        )

        if value is None:
            return None

        return str(value).strip() or None

    # =========================================================
    # CONTENT CONTAINER
    # =========================================================

    def _get_content_container(
        self,
        soup: BeautifulSoup,
        is_video: bool = False,
    ) -> Optional[Tag]:

        if is_video:
            selectors = [
                "div.ArticleDetails.details",
                "div.mainArticleContent",
                "article.articleVideoProgram",
            ]

        else:
            selectors = [
                "div.article-body-wrap",
                "div.ArticleDetails.details",
            ]

        for selector in selectors:
            container = soup.select_one(selector)

            if container:
                return container

        return None

    # =========================================================
    # CONTENT CLEANING
    # =========================================================

    def _remove_unwanted_elements(
        self,
        container: Tag,
    ) -> None:
        """
        Remove elements that should not be part of article content.
        """

        unwanted_selectors = [
            "script",
            "style",
            "iframe",
            "button",
            "form",
            "nav",
            "footer",
            "header",
            ".social-share",
            ".share-buttons",
            ".related-news",
            ".related-articles",
            ".recommended-articles",
            ".advertisement",
            ".ads",
            ".article-tools",
            ".print",
            ".comments",
        ]

        for selector in unwanted_selectors:
            for element in container.select(selector):
                element.decompose()

    def _extract_article_content(
        self,
        soup: BeautifulSoup,
        is_video: bool = False,
    ) -> Optional[str]:
        """
        Extract the article's actual text.

        Important:
        - Keeps paragraphs.
        - Keeps genuine h2/h3 article headings.
        - Stops when related-news content begins.
        - Preserves bank names and their values.
        - Avoids duplicate nested text.
        """

        container = self._get_content_container(
            soup,
            is_video=is_video,
        )

        if not container:
            return None

        self._remove_unwanted_elements(container)

        extracted_paragraphs = []
        seen_texts = set()

        content_tags = container.find_all(
            ["p", "h2", "h3"],
        )

        for element in content_tags:
            text = self._normalize_text(
                element.get_text(" ", strip=True)
            )

            if not text:
                continue

            # Stop completely when related news starts.
            if self._is_related_content_heading(text):
                break

            if self._is_noise_text(text):
                continue

            # Avoid repeated text.
            normalized_key = self._normalize_arabic_heading(text)

            if normalized_key in seen_texts:
                continue

            seen_texts.add(normalized_key)

            # Preserve meaningful article headings.
            if element.name in {"h2", "h3"}:
                extracted_paragraphs.append(text)
                continue

            # Ignore very short accidental UI fragments.
            if len(text) < 2:
                continue

            extracted_paragraphs.append(text)

        if not extracted_paragraphs:
            return None

        return "\n\n".join(extracted_paragraphs)

    # =========================================================
    # VIDEO DETECTION
    # =========================================================

    def _is_video_page(
        self,
        soup: BeautifulSoup,
        json_ld: dict[str, Any],
        url: str,
    ) -> bool:

        raw_type = json_ld.get("@type", [])

        if isinstance(raw_type, str):
            types = {raw_type}
        elif isinstance(raw_type, list):
            types = set(raw_type)
        else:
            types = set()

        if "VideoObject" in types:
            return True

        if self._is_valid_video_url(url):
            return True

        if soup.select_one("article.articleVideoProgram"):
            return True

        return False

    # =========================================================
    # ARTICLE EXTRACTION
    # =========================================================

    def _extract_article(
        self,
        url: str,
    ) -> Optional[RawArticle]:

        html = self._fetch_page(url)

        if not html:
            print(f"Unable to fetch article: {url}")
            return None

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        json_ld = self._extract_json_ld(
            soup
        )

        is_video = self._is_video_page(
            soup,
            json_ld,
            url,
        )

        title = self._extract_title(
            soup,
            json_ld,
        )

        if not title:
            print(f"Missing title: {url}")
            return None

        description = self._extract_description(
            soup,
            json_ld,
        )

        content = json_ld.get(
            "articleBody"
        )

        if isinstance(content, str):
            content = self._normalize_text(
                content
            )
        else:
            content = None

        # Prefer extracted HTML content when JSON-LD is empty.
        if not content:
            content = self._extract_article_content(
                soup,
                is_video=is_video,
            )

        if content:
            content = content.strip()

        # Preserve original date values before parsing.
        raw_publication_text = (
            self._extract_publication_date_text(
                json_ld,
                soup,
            )
        )

        publication_date = (
            self._parse_datetime(
                raw_publication_text
            )
        )

        raw_update_text = (
            self._extract_updated_at_text(
                json_ld,
                soup,
            )
        )

        updated_at = (
            self._parse_datetime(
                raw_update_text
            )
        )

        author = self._extract_author(
            json_ld,
            soup,
        )

        category = json_ld.get(
            "articleSection"
        )

        if isinstance(category, list):
            category = ", ".join(
                str(item)
                for item in category
            )

        if is_video:
            category = (
                category
                or "Masrawy TV"
            )

        category = (
            self._normalize_text(
                category
            )
            or None
        )

        # ---------------------------------------------------------
        # Extract article image URL.
        # ---------------------------------------------------------

        image_url = self._extract_image_url(
            json_ld=json_ld,
            soup=soup,
            article_url=url,
            is_video=is_video,
        )

        if image_url:
            print(
                "Article image found:",
                image_url,
            )
        else:
            print(
                "Warning: article image "
                "could not be extracted."
            )

        # Some pages do not expose publication dates.
        # Do not fabricate publication timestamps or reject
        # the article.
        if publication_date is None:
            print(
                "Warning: publication date unavailable "
                f"or invalid: {url}"
            )

        article = RawArticle(
            title=title,
            source=self.source_name,
            url=url,
            publication_date=publication_date,
            raw_publication_text=raw_publication_text,
            raw_update_text=raw_update_text,
            updated_at=updated_at,
            category=category,
            author=author,
            description=description,
            content=content,

            # Store the original article image URL.
            image_url=image_url,

            scraped_at=datetime.now(
                timezone.utc
            ),
            raw_html=html,
        )

        self._print_content_diagnostics(
            soup=soup,
            content=content,
            is_video=is_video,
        )

        return article

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def _print_content_diagnostics(
        self,
        soup: BeautifulSoup,
        content: Optional[str],
        is_video: bool,
    ) -> None:

        container = self._get_content_container(
            soup,
            is_video=is_video,
        )

        paragraphs = []

        if container:
            for element in container.find_all(
                ["p", "h2", "h3"],
            ):
                text = self._normalize_text(
                    element.get_text(
                        " ",
                        strip=True,
                    )
                )

                if text:
                    paragraphs.append(text)

        content_paragraphs = (
            content.split("\n\n")
            if content
            else []
        )

        print(
            "\n========== MASRAWY CONTENT DIAGNOSTICS =========="
        )

        print(
            f"Page type: "
            f"{'VIDEO' if is_video else 'NEWS ARTICLE'}"
        )

        if container:
            print(
                "Content container:",
                container.name,
                container.get("class", []),
            )
        else:
            print(
                "Content container: NOT FOUND"
            )

        print(
            "JSON-LD articleBody length:",
            0,
            "characters",
        )

        print(
            "HTML paragraphs found:",
            len(paragraphs),
        )

        print(
            "HTML paragraphs total length:",
            sum(
                len(item)
                for item in paragraphs
            ),
            "characters",
        )

        print(
            "Extracted content length:",
            len(content or ""),
            "characters",
        )

        print(
            "Extracted paragraphs count:",
            len(content_paragraphs),
        )

        print(
            "\nFirst 5 extracted paragraphs:"
        )

        for paragraph in content_paragraphs[:5]:
            print(
                "-",
                paragraph[:300],
            )

        print(
            "\nLast 3 extracted paragraphs:"
        )

        for paragraph in content_paragraphs[-3:]:
            print(
                "-",
                paragraph[:300],
            )

        print(
            "\n=================================================\n"
        )

    # =========================================================
    # MAIN SCRAPE
    # =========================================================

    def scrape(self) -> list[RawArticle]:
        print(
            "Fetching Masrawy homepage..."
        )

        homepage_html = self._fetch_page(
            self.HOMEPAGE_URL
        )

        if not homepage_html:
            print(
                "Unable to fetch Masrawy homepage."
            )
            return []

        article_urls = (
            self._extract_article_urls(
                homepage_html
            )
        )

        print(
            f"Valid article URLs found: "
            f"{len(article_urls)}"
        )

        selected_urls = article_urls[
            :self.MAX_ARTICLES
        ]

        print(
            f"Articles to scrape: "
            f"{len(selected_urls)}"
        )

        articles = []

        for index, url in enumerate(
            selected_urls,
            start=1,
        ):
            print(
                f"\n[{index}/{len(selected_urls)}] "
                "Scraping:"
            )

            print(url)

            try:
                article = self._extract_article(
                    url
                )

                if article:
                    articles.append(
                        article
                    )

                    print(
                        "Successfully scraped:"
                    )

                    print(
                        "Title:",
                        article.title,
                    )

                    print(
                        "Category:",
                        article.category,
                    )

                    print(
                        "Image URL:",
                        article.image_url,
                    )

                    print(
                        "Content length:",
                        len(
                            article.content
                            or ""
                        ),
                    )

                else:
                    print(
                        "Article extraction failed."
                    )

            except Exception as exc:
                print(
                    f"Error scraping article "
                    f"{url}: {exc}"
                )

            # Respectful delay between requests.
            if index < len(selected_urls):
                time.sleep(1)

        print(
            "\n========== MASRAWY SCRAPING SUMMARY =========="
        )

        print(
            "Articles found:",
            len(article_urls),
        )

        print(
            "Articles selected:",
            len(selected_urls),
        )

        print(
            "Articles successfully scraped:",
            len(articles),
        )

        print(
            "==============================================\n"
        )

        return articles