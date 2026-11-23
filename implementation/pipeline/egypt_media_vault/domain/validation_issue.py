from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class ValidationIssue:
    """
    Represents a validation problem found during article processing.

    An issue does not necessarily stop the entire pipeline.
    The validator can record the problem and decide whether the
    affected article should be rejected or allowed to continue.
    """

    field_name: str
    issue_type: str
    message: str

    severity: str = "error"
    article_url: Optional[str] = None
    detected_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Normalize and validate basic issue metadata."""

        self.field_name = self.field_name.strip()
        self.issue_type = self.issue_type.strip()
        self.message = self.message.strip()
        self.severity = self.severity.strip().lower()

        allowed_severities = {"warning", "error", "critical"}

        if self.severity not in allowed_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Expected one of: {sorted(allowed_severities)}"
            )

        if not self.field_name:
            raise ValueError("field_name cannot be empty.")

        if not self.issue_type:
            raise ValueError("issue_type cannot be empty.")

        if not self.message:
            raise ValueError("message cannot be empty.")