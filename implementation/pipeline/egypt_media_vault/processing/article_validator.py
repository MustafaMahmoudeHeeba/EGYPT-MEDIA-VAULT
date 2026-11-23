
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlsplit

from pipeline.egypt_media_vault.domain.raw_article import RawArticle
from pipeline.egypt_media_vault.domain.validation_issue import ValidationIssue


class ArticleValidator:
    """
    Validates raw articles before normalization and storage.

    Required fields:
        - title
        - source
        - url

    Publication date issues are non-rejecting warnings.
    The validator collects issues without modifying the original article.
    """

    def validate(self, article: RawArticle) -> list[ValidationIssue]:
        """
        Validate one raw article and return all detected issues.
        """

        issues: list[ValidationIssue] = []

        article_url = (
            article.url.strip()
            if isinstance(article.url, str)
            else None
        )

        # 1. Required string fields
        required_fields = {
            "title": article.title,
            "source": article.source,
            "url": article.url,
        }

        for field_name, value in required_fields.items():
            if not isinstance(value, str):
                issues.append(
                    self._create_issue(
                        field_name=field_name,
                        issue_type="invalid_type",
                        message=f"{field_name} must be a string.",
                        article_url=article_url,
                    )
                )

            elif not value.strip():
                issues.append(
                    self._create_issue(
                        field_name=field_name,
                        issue_type="missing_required_value",
                        message=f"{field_name} cannot be empty.",
                        article_url=article_url,
                    )
                )

        # 2. URL validation
        if isinstance(article.url, str) and article.url.strip():
            if not self._is_valid_url(article.url):
                issues.append(
                    self._create_issue(
                        field_name="url",
                        issue_type="invalid_url",
                        message="Article URL must be a valid HTTP or HTTPS URL.",
                        article_url=article_url,
                    )
                )

        # 3. Publication date validation
        # Missing or invalid publication dates must not reject an article.
        if article.publication_date is None:
            issues.append(
                self._create_issue(
                    field_name="publication_date",
                    issue_type="missing_publication_date",
                    message="Publication date is missing.",
                    severity="warning",
                    article_url=article_url,
                )
            )

        elif not isinstance(article.publication_date, datetime):
            issues.append(
                self._create_issue(
                    field_name="publication_date",
                    issue_type="invalid_type",
                    message="publication_date must be a datetime object or None.",
                    severity="warning",
                    article_url=article_url,
                )
            )

        elif not self._is_timezone_aware(article.publication_date):
            issues.append(
                self._create_issue(
                    field_name="publication_date",
                    issue_type="missing_timezone",
                    message="Publication date does not include timezone information.",
                    severity="warning",
                    article_url=article_url,
                )
            )

        else:
            now = datetime.now(timezone.utc)
            publication_date_utc = article.publication_date.astimezone(
                timezone.utc
            )

            if publication_date_utc > now:
                issues.append(
                    self._create_issue(
                        field_name="publication_date",
                        issue_type="future_publication_date",
                        message="Publication date is in the future.",
                        severity="warning",
                        article_url=article_url,
                    )
                )

        # 4. Optional datetime fields
        datetime_fields = {
            "updated_at": article.updated_at,
            "scraped_at": article.scraped_at,
        }

        for field_name, value in datetime_fields.items():
            if value is None:
                continue

            if not isinstance(value, datetime):
                issues.append(
                    self._create_issue(
                        field_name=field_name,
                        issue_type="invalid_type",
                        message=f"{field_name} must be a datetime object.",
                        article_url=article_url,
                    )
                )

            elif not self._is_timezone_aware(value):
                issues.append(
                    self._create_issue(
                        field_name=field_name,
                        issue_type="missing_timezone",
                        message=f"{field_name} must include timezone information.",
                        article_url=article_url,
                    )
                )

        # 5. Future scraped_at validation
        if (
            isinstance(article.scraped_at, datetime)
            and self._is_timezone_aware(article.scraped_at)
        ):
            scraped_at_utc = article.scraped_at.astimezone(timezone.utc)

            if scraped_at_utc > datetime.now(timezone.utc):
                issues.append(
                    self._create_issue(
                        field_name="scraped_at",
                        issue_type="future_scraped_at",
                        message="Scraped timestamp is in the future.",
                        severity="warning",
                        article_url=article_url,
                    )
                )

        # 6. Updated date consistency
        if (
            isinstance(article.publication_date, datetime)
            and self._is_timezone_aware(article.publication_date)
            and isinstance(article.updated_at, datetime)
            and self._is_timezone_aware(article.updated_at)
        ):
            publication_date_utc = article.publication_date.astimezone(
                timezone.utc
            )
            updated_at_utc = article.updated_at.astimezone(timezone.utc)

            if updated_at_utc < publication_date_utc:
                issues.append(
                    self._create_issue(
                        field_name="updated_at",
                        issue_type="date_before_publication",
                        message="updated_at cannot be earlier than publication_date.",
                        severity="warning",
                        article_url=article_url,
                    )
                )

        # 7. Optional text fields
        optional_text_fields = {
            "category": article.category,
            "author": article.author,
            "description": article.description,
            "content": article.content,
            "raw_html": article.raw_html,
            "raw_publication_text": article.raw_publication_text,
            "raw_update_text": article.raw_update_text,
        }

        for field_name, value in optional_text_fields.items():
            if value is not None and not isinstance(value, str):
                issues.append(
                    self._create_issue(
                        field_name=field_name,
                        issue_type="invalid_type",
                        message=f"{field_name} must be a string or None.",
                        article_url=article_url,
                    )
                )

        return issues

    @staticmethod
    def is_valid(issues: list[ValidationIssue]) -> bool:
        """
        An article is valid when it has no error or critical issues.
        Warnings do not reject the article.
        """

        return not any(
            issue.severity in {"error", "critical"}
            for issue in issues
        )

    @staticmethod
    def _is_valid_url(url: str) -> bool:
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
    def _is_timezone_aware(value: datetime) -> bool:
        return (
            value.tzinfo is not None
            and value.utcoffset() is not None
        )

    @staticmethod
    def _create_issue(
        field_name: str,
        issue_type: str,
        message: str,
        severity: str = "error",
        article_url: Optional[str] = None,
    ) -> ValidationIssue:

        return ValidationIssue(
            field_name=field_name,
            issue_type=issue_type,
            message=message,
            severity=severity,
            article_url=article_url,
            detected_at=datetime.now(timezone.utc),
        )
