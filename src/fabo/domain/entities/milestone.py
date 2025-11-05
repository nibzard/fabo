"""Milestone domain entity.

This module defines the core Milestone entity which represents a social media
milestone event that has been detected and potentially captured.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from fabo.domain.value_objects.milestone_type import MilestoneType, PlatformType


class Milestone(BaseModel):
    """Represents a social media milestone event.

    A milestone is created when a tracked metric reaches a predefined threshold.
    This entity contains all information about the milestone, including metadata
    about when it was detected and captured.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique milestone identifier")
    platform: PlatformType = Field(..., description="Platform where milestone occurred")
    milestone_type: MilestoneType = Field(..., description="Type of milestone")
    threshold_value: int = Field(..., gt=0, description="The threshold value reached")
    actual_value: int = Field(..., gt=0, description="The actual value when detected")
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the milestone was detected",
    )
    screenshot_id: UUID | None = Field(None, description="ID of associated screenshot")
    screenshot_captured: bool = Field(False, description="Whether screenshot was captured")
    screenshot_url: str | None = Field(None, description="URL that was screenshotted")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional platform-specific metadata",
    )
    notified: bool = Field(False, description="Whether user was notified")

    class Config:
        """Pydantic model configuration."""

        frozen = False  # Allow updates for screenshot_id, notified, etc.

    def is_new(self) -> bool:
        """Check if this is a newly detected milestone.

        Returns:
            True if the milestone was detected in the last minute.
        """
        age = datetime.now(timezone.utc) - self.detected_at
        return age.total_seconds() < 60

    def should_notify(self) -> bool:
        """Check if user should be notified about this milestone.

        Returns:
            True if milestone hasn't been notified yet.
        """
        return not self.notified

    def mark_screenshot_captured(self, screenshot_id: UUID, screenshot_url: str) -> None:
        """Mark that screenshot has been captured for this milestone.

        Args:
            screenshot_id: The unique ID of the screenshot.
            screenshot_url: The URL that was screenshotted.
        """
        object.__setattr__(self, "screenshot_id", screenshot_id)
        object.__setattr__(self, "screenshot_captured", True)
        object.__setattr__(self, "screenshot_url", screenshot_url)

    def mark_notified(self) -> None:
        """Mark that user has been notified about this milestone."""
        object.__setattr__(self, "notified", True)

    def get_display_text(self) -> str:
        """Get a human-readable display text for this milestone.

        Returns:
            A formatted string describing the milestone.
        """
        return (
            f"{self.platform.value.title()} {self.milestone_type.metric_name}: "
            f"{self.actual_value:,} (threshold: {self.threshold_value:,})"
        )

    def __str__(self) -> str:
        """Return string representation of the milestone."""
        return self.get_display_text()
