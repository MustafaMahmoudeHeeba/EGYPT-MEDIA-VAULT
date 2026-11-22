import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from pipeline.egypt_media_vault.domain.raw_article import RawArticle
from pipeline.egypt_media_vault.scrapers.base_scraper import BaseScraper
from pipeline.egypt_media_vault.scrapers.http_client import HttpClient


class AlMasryAlYoumScraper(BaseScraper):
    """
    Scraper for Al-Masry Al-Youm.

    Responsibilities:
    - Discover valid article URLs.
    - Extract article metadata from JSON-LD.
    - Extract article image URL.
    - Extract article content from the HTML page.
    - Exclude embedded X/Twitter posts from article content.
    - Preserve the original HTML exactly as received.
    """

    def __init__(self) -> None:
        super().__init__("almasryalyoum")

        self.base_url = "https://www.almasryalyoum.com/"
        self.http_client = HttpClient()

    def scrape(self) -> list[RawArticle]:
        """Scrape articles from Al-Masry Al-Youm."""

        print("Fetching Al-Masry Al-Youm homepage...")

        homepage_html = self.http_client.get(
            self.base_url
        )

        article_urls = self._extract_article_urls(
            homepage_html
        )

        print(
            f"Valid article URLs found: "
            f"{len(article_urls)}"
        )

        # Temporary diagnostic limit.
        article_urls = article_urls[:1]

        print(
            f"Articles to scrape: "
            f"{len(article_urls)}"
        )

        articles: list[RawArticle] = []

        for index, url in enumerate(
            article_urls,
            start=1,
        ):
            print(
                f"[{index}/{len(article_urls)}] "
                "Scraping article:"
            )
            print(f"    {url}")

            article = self._scrape_article(url)

            if article is not None:
                articles.append(article)

                print(
                    "    ✓ Article extracted successfully"
                )
            else:
                print(
                    "    ✗ Article extraction failed"
                )

        print()
        print(
            f"Successfully scraped: "
            f"{len(articles)} articles"
        )

        return articles

    def _extract_article_urls(
        self,
        html: str,
    ) -> list[str]:
        """Extract valid article URLs from homepage."""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        article_urls: list[str] = []
        seen_urls: set[str] = set()

        for link in soup.find_all(
            "a",
            href=True,
        ):
            href = link.get("href")

            if not href:
                continue

            url = urljoin(
                self.base_url,
                href,
            )

            if not self._is_article_url(url):
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)
            article_urls.append(url)

        return article_urls

    def _scrape_article(
        self,
        url: str,
    ) -> RawArticle | None:
        """Scrape one article page."""

        try:
            html = self.http_client.get(url)

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            article_data = (
                self._extract_article_data(soup)
            )

            if article_data is None:
                print(
                    "    No structured article data found"
                )
                return None

            # Temporary content diagnostics.
            self._print_content_diagnostics(
                soup,
                article_data,
            )

            title = article_data.get(
                "headline"
            )

            if not title:
                print(
                    "    Article title not found"
                )
                return None

            # Preserve original date values before parsing.
            raw_publication_text = article_data.get(
                "datePublished"
            )

            publication_date = self._parse_datetime(
                raw_publication_text
            )

            raw_update_text = article_data.get(
                "dateModified"
            )

            updated_at = self._parse_datetime(
                raw_update_text
            )

            if publication_date is None:
                print(
                    "    Warning: publication date unavailable or invalid"
                )

            # Detect embedded X/Twitter posts.
            twitter_posts = soup.select(
                "blockquote.twitter-tweet"
            )

            if twitter_posts:
                print(
                    f"    Found {len(twitter_posts)} "
                    "embedded X posts. Excluding them from article content."
                )

                # Extract content from a clean HTML copy.
                # The original soup and raw HTML remain untouched.
                content = (
                    self._extract_article_content_without_social_embeds(
                        soup
                    )
                )

            else:
                # Try JSON-LD first when no embedded X posts exist.
                content = article_data.get(
                    "articleBody"
                )

                # Fallback to HTML extraction.
                if not content:
                    content = (
                        self._extract_article_content(
                            soup
                        )
                    )

            if content:
                print(
                    f"    Content extracted: "
                    f"{len(content)} characters"
                )
            else:
                print(
                    "    Warning: article content "
                    "could not be extracted"
                )

            article_url = (
                article_data.get("url")
                or url
            )

            # Extract article image URL.
            image_url = self._extract_image_url(
                article_data=article_data,
                soup=soup,
                article_url=article_url,
            )

            if image_url:
                print(
                    "    Article image found:"
                    f" {image_url}"
                )
            else:
                print(
                    "    Warning: article image "
                    "could not be extracted"
                )

            return RawArticle(
                title=title,
                source=self.source_name,
                url=article_url,
                publication_date=publication_date,
                raw_publication_text=raw_publication_text,
                raw_update_text=raw_update_text,
                updated_at=updated_at,
                category=(
                    article_data.get(
                        "articleSection"
                    )
                ),
                author=self._extract_author(
                    article_data.get(
                        "author"
                    )
                ),
                description=(
                    article_data.get(
                        "description"
                    )
                ),
                content=content,
                image_url=image_url,
                scraped_at=datetime.now(
                    timezone.utc
                ),
                raw_html=html,
            )

        except Exception as exc:
            print(
                f"    Failed to scrape article: "
                f"{url}"
            )

            print(
                f"    Reason: {exc}"
            )

            return None

    # =========================================================
    # IMAGE EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_image_from_json_ld(
        image_data: object,
    ) -> str | None:
        """
        Extract an image URL from the JSON-LD image field.

        Supported formats:
        - String URL.
        - Dictionary containing url/contentUrl.
        - List of strings/dictionaries.
        """

        if isinstance(
            image_data,
            str,
        ):
            value = image_data.strip()

            return value or None

        if isinstance(
            image_data,
            dict,
        ):
            for key in (
                "url",
                "contentUrl",
            ):
                value = image_data.get(
                    key
                )

                if isinstance(
                    value,
                    str,
                ):
                    value = value.strip()

                    if value:
                        return value

        if isinstance(
            image_data,
            list,
        ):
            for item in image_data:

                result = (
                    AlMasryAlYoumScraper
                    ._extract_image_from_json_ld(
                        item
                    )
                )

                if result:
                    return result

        return None

    @staticmethod
    def _extract_image_src(
        image,
    ) -> str | None:
        """
        Extract the actual image source from an
        HTML img element.

        Supports normal src, lazy-loaded attributes,
        and srcset.
        """

        attributes = [
            "src",
            "data-src",
            "data-original",
            "data-lazy-src",
            "data-image",
        ]

        for attribute in attributes:

            value = image.get(
                attribute
            )

            if isinstance(
                value,
                str,
            ):
                value = value.strip()

                if value:
                    return value

        # Fallback to srcset.
        srcset = image.get(
            "srcset"
        )

        if isinstance(
            srcset,
            str,
        ):
            candidates = [
                item.strip()
                for item in srcset.split(",")
                if item.strip()
            ]

            if candidates:
                # Usually the last candidate is
                # the highest resolution image.
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

        if lowered.startswith(
            "data:"
        ):
            return False

        if lowered.startswith(
            "javascript:"
        ):
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
        article_data: dict,
        soup: BeautifulSoup,
        article_url: str,
    ) -> str | None:
        """
        Extract the article image URL.

        Extraction order:
        1. JSON-LD image.
        2. Open Graph og:image.
        3. Twitter image.
        4. Image inside the article container.
        5. General article-page image fallback.

        Returns:
            Absolute image URL or None.
        """

        # ---------------------------------------------------------
        # 1. JSON-LD image
        # ---------------------------------------------------------

        json_ld_image = (
            self._extract_image_from_json_ld(
                article_data.get(
                    "image"
                )
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

        og_image = soup.find(
            "meta",
            attrs={
                "property": "og:image"
            },
        )

        if og_image:
            content = og_image.get(
                "content"
            )

            if isinstance(
                content,
                str,
            ):
                content = content.strip()

                if (
                    content
                    and self._is_valid_image_url(
                        content
                    )
                ):
                    return urljoin(
                        article_url,
                        content,
                    )

        # ---------------------------------------------------------
        # 3. Twitter image
        # ---------------------------------------------------------

        twitter_image = soup.find(
            "meta",
            attrs={
                "name": "twitter:image"
            },
        )

        if twitter_image:
            content = twitter_image.get(
                "content"
            )

            if isinstance(
                content,
                str,
            ):
                content = content.strip()

                if (
                    content
                    and self._is_valid_image_url(
                        content
                    )
                ):
                    return urljoin(
                        article_url,
                        content,
                    )

        # ---------------------------------------------------------
        # 4. Image inside article containers
        # ---------------------------------------------------------

        selectors = [
            "article img",
            "[class*='article-content'] img",
            "[class*='article_body'] img",
            "[class*='article-body'] img",
            "[class*='articleBody'] img",
            "[class*='article__body'] img",
            "[class*='article-text'] img",
            "[class*='article-details'] img",
            "[class*='news-content'] img",
            "[class*='news-body'] img",
            "[class*='content-body'] img",
            "[class*='story-content'] img",
            "[class*='story-body'] img",
        ]

        for selector in selectors:

            images = soup.select(
                selector
            )

            for image in images:

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
        # 5. General page fallback
        # ---------------------------------------------------------

        for image in soup.find_all(
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

        return None

    @staticmethod
    def _print_content_diagnostics(
        soup: BeautifulSoup,
        article_data: dict,
    ) -> None:
        """
        Compare JSON-LD content with HTML paragraphs
        and inspect the existing HTML extraction.
        """

        json_body = article_data.get(
            "articleBody"
        ) or ""

        if not isinstance(
            json_body,
            str,
        ):
            json_body = str(
                json_body
            )

        paragraphs = soup.find_all(
            "p"
        )

        paragraph_texts = [
            paragraph.get_text(
                " ",
                strip=True,
            )
            for paragraph in paragraphs
            if len(
                paragraph.get_text(
                    " ",
                    strip=True,
                )
            ) > 40
        ]

        html_content = "\n".join(
            paragraph_texts
        )

        extracted_html_content = (
            AlMasryAlYoumScraper
            ._extract_article_content(
                soup
            )
            or ""
        )

        print(
            "\n========== CONTENT DIAGNOSTICS =========="
        )

        print(
            f"JSON-LD content length: "
            f"{len(json_body)} characters"
        )

        print(
            f"HTML paragraphs found: "
            f"{len(paragraph_texts)}"
        )

        print(
            f"HTML paragraphs total length: "
            f"{len(html_content)} characters"
        )

        print(
            f"Existing HTML extraction length: "
            f"{len(extracted_html_content)} characters"
        )

        print("\nJSON-LD content preview:")
        print(
            json_body[:500]
            if json_body
            else "[EMPTY]"
        )

        print("\nFirst 5 HTML paragraphs:")

        for paragraph in paragraph_texts[:5]:
            print(
                f"- {paragraph[:250]}"
            )

        extracted_paragraphs = [
            paragraph.strip()
            for paragraph in extracted_html_content.split(
                "\n"
            )
            if paragraph.strip()
        ]

        print(
            f"\nExtracted paragraphs count: "
            f"{len(extracted_paragraphs)}"
        )

        print("\nFirst 10 extracted paragraphs:")

        for paragraph in extracted_paragraphs[:10]:
            print(
                f"- {paragraph[:300]}"
            )

        print("\nLast 3 extracted paragraphs:")

        for paragraph in extracted_paragraphs[-3:]:
            print(
                f"- {paragraph[:300]}"
            )

        print(
            "\n========================================\n"
        )

    @staticmethod
    def _extract_article_data(
        soup: BeautifulSoup,
    ) -> dict | None:
        """Extract article metadata from JSON-LD."""

        for script in soup.find_all(
            "script",
            type="application/ld+json",
        ):
            raw_json = script.get_text(
                strip=True
            )

            if not raw_json:
                continue

            try:
                data = json.loads(
                    raw_json
                )

            except json.JSONDecodeError:
                continue

            candidates = (
                data
                if isinstance(
                    data,
                    list,
                )
                else [data]
            )

            for item in candidates:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                article_type = item.get(
                    "@type"
                )

                if article_type in {
                    "NewsArticle",
                    "Article",
                }:
                    return item

                if isinstance(
                    article_type,
                    list,
                ):
                    if (
                        "NewsArticle"
                        in article_type
                        or "Article"
                        in article_type
                    ):
                        return item

        return None

    @staticmethod
    def _extract_article_content_without_social_embeds(
        soup: BeautifulSoup,
    ) -> str | None:
        """
        Extract article content after removing embedded
        X/Twitter posts from a separate HTML copy.

        The original soup and raw HTML remain untouched.
        """

        clean_soup = BeautifulSoup(
            str(soup),
            "html.parser",
        )

        for element in clean_soup.select(
            "blockquote.twitter-tweet"
        ):
            element.decompose()

        return (
            AlMasryAlYoumScraper
            ._extract_article_content(
                clean_soup
            )
        )

    @staticmethod
    def _extract_article_content(
        soup: BeautifulSoup,
    ) -> str | None:
        """
        Extract article body from the HTML.
        """

        selectors = [
            "article",
            "[class*='article-content']",
            "[class*='article_body']",
            "[class*='article-body']",
            "[class*='articleBody']",
            "[class*='article__body']",
            "[class*='article-text']",
            "[class*='article-texts']",
            "[class*='article-details']",
            "[class*='article-details-content']",
            "[class*='news-content']",
            "[class*='news-body']",
            "[class*='content-body']",
            "[class*='story-content']",
            "[class*='story-body']",
        ]

        for selector in selectors:

            containers = soup.select(
                selector
            )

            for container in containers:

                content = (
                    AlMasryAlYoumScraper
                    ._extract_paragraphs(
                        container
                    )
                )

                if (
                    content
                    and len(content) >= 200
                ):
                    return content

        heading = soup.find(
            "h1"
        )

        if heading:

            paragraphs: list[str] = []

            for element in heading.find_all_next():

                if element.name == "p":

                    text = element.get_text(
                        " ",
                        strip=True,
                    )

                    if (
                        text
                        and len(text) >= 20
                        and not AlMasryAlYoumScraper._is_noise_text(
                            text
                        )
                    ):
                        paragraphs.append(
                            text
                        )

                if element.name == "footer":
                    break

            content = "\n".join(
                paragraphs
            )

            if len(content) >= 200:
                return content

        all_paragraphs = soup.find_all(
            "p"
        )

        paragraph_texts: list[str] = []

        for paragraph in all_paragraphs:

            text = paragraph.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            if len(text) < 20:
                continue

            if AlMasryAlYoumScraper._is_noise_text(
                text
            ):
                continue

            paragraph_texts.append(
                text
            )

        if paragraph_texts:

            content = "\n".join(
                paragraph_texts
            )

            if len(content) >= 200:
                return content

        return None

    @staticmethod
    def _extract_paragraphs(
        container,
    ) -> str | None:
        """Extract meaningful paragraphs from an article container."""

        container = BeautifulSoup(
            str(container),
            "html.parser",
        )

        for unwanted in container.find_all(
            [
                "script",
                "style",
                "noscript",
                "iframe",
                "form",
                "nav",
                "header",
                "footer",
                "button",
            ]
        ):
            unwanted.decompose()

        paragraphs = container.find_all(
            "p"
        )

        texts: list[str] = []

        for paragraph in paragraphs:

            text = paragraph.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            if len(text) < 20:
                continue

            if AlMasryAlYoumScraper._is_noise_text(
                text
            ):
                continue

            texts.append(text)

        if not texts:
            return None

        return "\n".join(texts)

    @staticmethod
    def _is_noise_text(
        text: str,
    ) -> bool:
        """Detect common navigation/UI text."""

        normalized = text.strip()

        noise_patterns = [
            "أخبار متعلقة",
            "إضافة المصري اليوم إلى المصادر المفضلة",
            "اشترك الآن",
            "تسجيل الدخول",
            "تسجيل دخول",
            "الأكثر قراءة",
            "اقرأ أيضًا",
            "تابعنا",
            "شارك",
            "جميع الحقوق محفوظة",
            "المزيد من الأخبار",
        ]

        for pattern in noise_patterns:

            if pattern in normalized:
                return True

        return False

    @staticmethod
    def _extract_author(
        author_data: object,
    ) -> str | None:
        """Extract author name from JSON-LD."""

        if isinstance(
            author_data,
            dict,
        ):
            name = author_data.get(
                "name"
            )

            if isinstance(
                name,
                str,
            ):
                return (
                    name.strip()
                    or None
                )

        if isinstance(
            author_data,
            list,
        ):
            names: list[str] = []

            for author in author_data:

                if isinstance(
                    author,
                    dict,
                ):
                    name = author.get(
                        "name"
                    )

                    if (
                        isinstance(
                            name,
                            str,
                        )
                        and name.strip()
                    ):
                        names.append(
                            name.strip()
                        )

                elif (
                    isinstance(
                        author,
                        str,
                    )
                    and author.strip()
                ):
                    names.append(
                        author.strip()
                    )

            if names:
                return ", ".join(
                    names
                )

        if isinstance(
            author_data,
            str,
        ):
            return (
                author_data.strip()
                or None
            )

        return None

    @staticmethod
    def _parse_datetime(
        value: object,
    ) -> datetime | None:
        """Parse an ISO-8601 datetime value."""

        if not isinstance(
            value,
            str,
        ):
            return None

        value = value.strip()

        if not value:
            return None

        try:

            parsed = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed

        except ValueError:
            return None

    @staticmethod
    def _is_article_url(
        url: str,
    ) -> bool:
        """Validate Al-Masry Al-Youm article URLs."""

        if not url:
            return False

        parsed = urlparse(
            url
        )

        if parsed.scheme != "https":
            return False

        if parsed.netloc != (
            "www.almasryalyoum.com"
        ):
            return False

        path = parsed.path.strip(
            "/"
        )

        if not path:
            return False

        article_pattern = re.compile(
            r"^news/details/\d+$",
            re.IGNORECASE,
        )

        return bool(
            article_pattern.fullmatch(
                path
            )
        )