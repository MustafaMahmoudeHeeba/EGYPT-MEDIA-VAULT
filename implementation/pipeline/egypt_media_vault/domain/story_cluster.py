
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass(slots=True)
class StoryCluster:
    """
    Represents a group of articles that refer to the same news story.

    A story cluster is created by the story matching process.
    Multiple articles from different news sources can belong
    to the same cluster.
    """

    cluster_id: str
    representative_title: str

    articles: List[str] = field(default_factory=list)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    similarity_threshold: float = 0.75

    def __post_init__(self) -> None:
        """Validate and normalize story cluster metadata."""

        self.cluster_id = self.cluster_id.strip()
        self.representative_title = self.representative_title.strip()

        if not self.cluster_id:
            raise ValueError("Story cluster ID cannot be empty.")

        if not self.representative_title:
            raise ValueError(
                "Story cluster representative title cannot be empty."
            )

        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError(
                "Similarity threshold must be between 0.0 and 1.0."
            )

        # Remove empty article IDs and duplicate IDs
        self.articles = list(
            dict.fromkeys(
                article_id.strip()
                for article_id in self.articles
                if article_id and article_id.strip()
            )
        )

    @property
    def article_count(self) -> int:
        """Return the number of articles in the cluster."""
        return len(self.articles)

    def add_article(self, article_id: str) -> None:
        """Add an article to the cluster if it is not already present."""

        article_id = article_id.strip()

        if not article_id:
            raise ValueError("Article ID cannot be empty.")

        if article_id not in self.articles:
            self.articles.append(article_id)

        self.updated_at = datetime.now(timezone.utc)

    def contains_article(self, article_id: str) -> bool:
        """Return True when the article belongs to this cluster."""
        return article_id in self.articles
