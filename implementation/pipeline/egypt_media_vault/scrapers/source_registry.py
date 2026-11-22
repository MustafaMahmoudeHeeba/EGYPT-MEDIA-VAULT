
from typing import Type

from pipeline.egypt_media_vault.scrapers.base_scraper import BaseScraper

from pipeline.egypt_media_vault.scrapers.sources.youm7_scraper import (
    Youm7Scraper,
)

from pipeline.egypt_media_vault.scrapers.sources.almasryalyoum_scraper import (
    AlMasryAlYoumScraper,
)

from pipeline.egypt_media_vault.scrapers.sources.masrawy_scraper import (
    MasrawyScraper,
)


# =========================================================
# SOURCE REGISTRY
# =========================================================

SCRAPER_REGISTRY: dict[str, Type[BaseScraper]] = {
    "youm7": Youm7Scraper,
    "almasryalyoum": AlMasryAlYoumScraper,
    "masrawy": MasrawyScraper,
}


# =========================================================
# REGISTRY VALIDATION
# =========================================================

def create_scrapers() -> list[tuple[str, BaseScraper]]:
    """
    Create all registered scrapers and verify that each
    scraper's source_name matches its registry identifier.
    """

    scrapers = []

    for source_id, scraper_class in SCRAPER_REGISTRY.items():

        scraper = scraper_class()

        if scraper.source_name != source_id:
            raise ValueError(
                f"Source registry mismatch: "
                f"registry ID '{source_id}' does not match "
                f"scraper source_name '{scraper.source_name}'."
            )

        scrapers.append((source_id, scraper))

    return scrapers
