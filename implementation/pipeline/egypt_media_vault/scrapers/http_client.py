import time

import requests

from pipeline.egypt_media_vault.config.settings import settings


class HttpClient:
    """
    Small HTTP client used by news scrapers.

    It centralizes request timeout, retry behavior,
    headers, and delay between requests.
    """

    def __init__(
        self,
        timeout: int | None = None,
        delay: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.timeout = (
            timeout
            if timeout is not None
            else settings.request_timeout_seconds
        )

        self.delay = (
            delay
            if delay is not None
            else settings.request_delay_seconds
        )

        self.max_retries = (
            max_retries
            if max_retries is not None
            else settings.max_retries
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/157.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ar-EG,ar;q=0.9,en;q=0.8",
            }
        )

    def get(self, url: str) -> str:
        """
        Fetch a URL and return its HTML content.

        Retries failed requests using a simple exponential backoff.
        """

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                time.sleep(self.delay)

                return response.text

            except requests.RequestException as exc:
                last_error = exc

                if attempt >= self.max_retries:
                    break

                wait_time = 2**attempt
                time.sleep(wait_time)

        raise RuntimeError(
            f"Failed to fetch URL after "
            f"{self.max_retries + 1} attempts: {url}"
        ) from last_error