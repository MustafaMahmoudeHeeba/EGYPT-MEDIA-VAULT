from abc import ABC, abstractmethod

from pipeline.egypt_media_vault.domain.raw_article import RawArticle


class BaseScraper(ABC):
    """
    Base class for Egyptian news website scrapers.

    Each concrete scraper is responsible for understanding
    the HTML structure of its own news source.
    """

    def __init__(self, source_name: str) -> None:
        self.source_name = source_name

    @abstractmethod
    def scrape(self) -> list[RawArticle]:
        """
        Scrape articles from the configured news source.

        Returns:
            A list of RawArticle objects.
        """
        raise NotImplementedError