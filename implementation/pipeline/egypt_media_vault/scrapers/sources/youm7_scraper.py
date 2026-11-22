import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from pipeline.egypt_media_vault.domain.raw_article import RawArticle
from pipeline.egypt_media_vault.scrapers.base_scraper import BaseScraper
from pipeline.egypt_media_vault.scrapers.http_client import HttpClient


class Youm7Scraper(BaseScraper):
    """
    Scraper for Youm7.
    """

    def __init__(self) -> None:
        super().__init__("youm7")

        self.base_url = "https://www.youm7.com/"
        self.http_client = HttpClient()

    def scrape(self) -> list[RawArticle]:
        """Scrape articles from the Youm7 homepage."""

        print("Fetching Youm7 homepage...")

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

        # Development limit: first article only.
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

            article = self._scrape_article(
                url
            )

            if article is not None:
                articles.append(article)

                print(
                    "    Article extracted successfully"
                )

            else:
                print(
                    "    Article extraction failed"
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
        """Extract valid Youm7 article URLs."""

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
        """Fetch and parse one Youm7 article page."""

        try:
            html = self.http_client.get(
                url
            )

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            article_data = (
                self._extract_news_article_json_ld(
                    soup
                )
            )

            if article_data is None:
                print(
                    "    No NewsArticle JSON-LD found"
                )

                return None

            title = article_data.get(
                "headline"
            )

            if not title:
                print(
                    "    Article title not found"
                )

                return None

            raw_publication_text = (
                article_data.get(
                    "datePublished"
                )
            )

            publication_date = (
                self._parse_datetime(
                    raw_publication_text
                )
            )

            raw_update_text = (
                article_data.get(
                    "dateModified"
                )
            )

            updated_at = (
                self._parse_datetime(
                    raw_update_text
                )
            )

            if publication_date is None:
                print(
                    "    Warning: publication date "
                    "unavailable or invalid"
                )

            author = self._extract_author(
                article_data.get(
                    "author"
                )
            )

            article_url = (
                article_data.get("url")
                or url
            )

            # Extract article image URL.
            # Prefer the NewsArticle JSON-LD image.
            image_url = self._extract_image_url(
                article_data.get("image"),
                soup,
                article_url,
            )

            if image_url:
                print(
                    f"    Article image found: "
                    f"{image_url}"
                )

            else:
                print(
                    "    Warning: article image "
                    "could not be extracted"
                )

            # Prefer actual article paragraphs.
            # JSON-LD is only a fallback because it may
            # contain unrelated text appended by the website.
            content = (
                self._extract_article_content(
                    soup
                )
            )

            if content:
                print(
                    f"    HTML article content extracted: "
                    f"{len(content)} characters"
                )

            else:
                content = (
                    article_data.get(
                        "articleBody"
                    )
                )

                if content:
                    print(
                        "    Using JSON-LD articleBody "
                        "as fallback"
                    )

                else:
                    print(
                        "    Warning: article content "
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
                category=article_data.get(
                    "articleSection"
                ),
                author=author,
                description=article_data.get(
                    "description"
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
                f"    Failed to scrape article: {url}"
            )

            print(
                f"    Reason: {exc}"
            )

            return None

    @staticmethod
    def _extract_image_url(
        image_data: object,
        soup: BeautifulSoup,
        article_url: str,
    ) -> str | None:
        """
        Extract the article image URL.

        Extraction order:
            1. NewsArticle JSON-LD image
            2. Open Graph og:image
            3. Twitter image
            4. Article container image
            5. First meaningful image inside the article

        Returns:
            Absolute image URL or None.
        """

        # ---------------------------------------------------------
        # 1. NewsArticle JSON-LD image
        # ---------------------------------------------------------

        json_ld_image = (
            Youm7Scraper._extract_image_from_json_ld(
                image_data
            )
        )

        if json_ld_image:
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

                if content:
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

                if content:
                    return urljoin(
                        article_url,
                        content,
                    )

        # ---------------------------------------------------------
        # 4. Article container images
        # ---------------------------------------------------------

        selectors = [
            "article .article-content img",
            "article .article-details img",
            "article [class*='article-content'] img",
            "article [class*='article-body'] img",
            "article img",
            "[class*='article-content'] img",
            "[class*='article-body'] img",
        ]

        for selector in selectors:

            images = soup.select(
                selector
            )

            for image in images:

                image_url = (
                    Youm7Scraper._extract_image_src(
                        image
                    )
                )

                if (
                    image_url
                    and Youm7Scraper._is_valid_image_url(
                        image_url
                    )
                ):
                    return urljoin(
                        article_url,
                        image_url,
                    )

        return None

    @staticmethod
    def _extract_image_from_json_ld(
        image_data: object,
    ) -> str | None:
        """
        Extract an image URL from the JSON-LD image field.

        The image field may be:
            - a string
            - a dictionary containing url/contentUrl
            - a list of strings/dictionaries
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
                    Youm7Scraper._extract_image_from_json_ld(
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

        Supports normal src, lazy-loaded src,
        srcset, and data attributes.
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

                # Select the last candidate,
                # which is commonly the highest
                # resolution image.
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
        Reject obvious non-image, placeholder,
        tracking, and data URLs.
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

    @staticmethod
    def _extract_article_content(
        soup: BeautifulSoup,
    ) -> str | None:
        """
        Extract article paragraphs from the actual
        article container, excluding related content
        and website footer elements.
        """

        selectors = [
            "article .article-content",
            "article .article-details",
            "article [class*='article-content']",
            "article [class*='article-body']",
            "article",
            "[class*='article-content']",
            "[class*='article-body']",
        ]

        for selector in selectors:

            containers = soup.select(
                selector
            )

            for container in containers:

                paragraphs = (
                    Youm7Scraper
                    ._extract_clean_paragraphs(
                        container
                    )
                )

                if paragraphs:
                    content = "\n".join(
                        paragraphs
                    )

                    if len(content) >= 100:
                        return content

        return None

    @staticmethod
    def _extract_clean_paragraphs(
        container,
    ) -> list[str]:
        """
        Extract meaningful paragraphs without
        navigation, related articles, or footer text.
        """

        clean_container = BeautifulSoup(
            str(container),
            "html.parser",
        )

        unwanted_selectors = [
            "script",
            "style",
            "noscript",
            "iframe",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "button",
            "[class*='related']",
            "[class*='recommend']",
            "[class*='most-read']",
            "[class*='social']",
            "[class*='share']",
            "[class*='comment']",
            "[class*='tags']",
        ]

        for selector in unwanted_selectors:

            for element in clean_container.select(
                selector
            ):
                element.decompose()

        paragraphs = clean_container.find_all(
            "p"
        )

        results: list[str] = []

        seen: set[str] = set()

        for paragraph in paragraphs:

            text = paragraph.get_text(
                " ",
                strip=True,
            )

            text = re.sub(
                r"\s+",
                " ",
                text,
            ).strip()

            if len(text) < 30:
                continue

            if Youm7Scraper._is_noise_text(
                text
            ):
                continue

            if text in seen:
                continue

            seen.add(text)
            results.append(text)

        return results

    @staticmethod
    def _is_noise_text(
        text: str,
    ) -> bool:
        """Identify common Youm7 non-article text."""

        noise_patterns = [
            "الموضوعات المتعلقة",
            "تم التصميم والتطوير بواسطة",
            "جميع الحقوق محفوظة",
            "اشترك الآن",
            "تسجيل الدخول",
            "تابعنا",
            "اقرأ أيضًا",
        ]

        return any(
            pattern in text
            for pattern in noise_patterns
        )

    @staticmethod
    def _extract_news_article_json_ld(
        soup: BeautifulSoup,
    ) -> dict | None:
        """Find the NewsArticle JSON-LD object."""

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
                if isinstance(data, list)
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

                if article_type == "NewsArticle":
                    return item

                if (
                    isinstance(
                        article_type,
                        list,
                    )
                    and "NewsArticle" in article_type
                ):
                    return item

        return None

    @staticmethod
    def _extract_author(
        author_data: object,
    ) -> str | None:
        """Extract the author name from JSON-LD."""

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
                return name.strip() or None

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
            return author_data.strip() or None

        return None

    @staticmethod
    def _parse_datetime(
        value: object,
    ) -> datetime | None:
        """Parse an ISO-8601 datetime string."""

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
        """Determine whether a URL is a valid Youm7 article URL."""

        if not url:
            return False

        if not url.startswith(
            "https://www.youm7.com/"
        ):
            return False

        if "/story/" not in url:
            return False

        path = url.split(
            "https://www.youm7.com/",
            1,
        )[1]

        parts = path.split("/")

        if len(parts) < 6:
            return False

        if parts[0].lower() != "story":
            return False

        year = parts[1]
        month = parts[2]
        day = parts[3]
        article_id = parts[-1]

        if not re.fullmatch(
            r"\d{4}",
            year,
        ):
            return False

        if not re.fullmatch(
            r"\d{1,2}",
            month,
        ):
            return False

        if not re.fullmatch(
            r"\d{1,2}",
            day,
        ):
            return False

        if not re.fullmatch(
            r"\d+",
            article_id,
        ):
            return False

        return True