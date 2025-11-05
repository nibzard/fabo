"""Operator state entity for tracking execution state between runs.

This entity maintains the state of an operator execution, enabling
smart optimization and continuation across multiple runs.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OperatorMode(str, Enum):
    """Operational mode for the operator."""

    API = "api"  # Using platform API for checks
    SCREENSHOT = "screenshot"  # Using screenshot + LLM extraction
    HYBRID = "hybrid"  # Both API and screenshot
    SCREENSHOT_ONLY = "screenshot_only"  # No API access, screenshot only


class OperatorState(BaseModel):
    """State tracking for operator execution.

    This entity persists between operator runs to enable:
    - Smart mode switching (API vs screenshot)
    - Rate limit management
    - Cost optimization
    - Continuous monitoring
    """

    # Identity
    id: UUID = Field(default_factory=uuid4, description="Unique state identifier")
    run_id: str = Field(..., description="Human-readable run identifier")
    platform: str = Field(..., description="Platform being monitored")

    # Target configuration
    target: dict[str, Any] = Field(..., description="Target configuration (repo, username, etc)")
    metric_name: str = Field(..., description="Primary metric being tracked")

    # Current state
    last_check: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the last check occurred",
    )
    current_value: int | None = Field(None, description="Last known metric value")
    mode: OperatorMode = Field(OperatorMode.API, description="Current operational mode")

    # Threshold management
    thresholds: list[int] = Field(..., description="All threshold values to monitor")
    next_threshold: int | None = Field(None, description="Next threshold to reach")
    milestone_reached: bool = Field(False, description="Whether milestone was captured")

    # Optimization settings
    check_interval: int = Field(
        3600, description="Current check interval in seconds"
    )
    threshold_proximity_percent: int = Field(
        90, ge=0, le=100, description="Proximity % to switch to screenshot mode"
    )
    api_mode_interval: int = Field(3600, description="Check interval for API mode")
    screenshot_mode_interval: int = Field(300, description="Check interval for screenshot mode")

    # Statistics
    total_checks: int = Field(0, description="Total number of checks performed")
    api_calls_made: int = Field(0, description="Number of API calls made")
    screenshots_taken: int = Field(0, description="Number of screenshots captured")
    llm_calls_made: int = Field(0, description="Number of LLM vision calls made")

    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this state was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this state was last updated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        """Pydantic configuration."""

        frozen = False  # Allow updates

    def calculate_proximity(self) -> float:
        """Calculate proximity to next threshold as percentage.

        Returns:
            Proximity percentage (0-100), or 0 if no threshold or current value.
        """
        if not self.next_threshold or not self.current_value:
            return 0.0

        if self.current_value >= self.next_threshold:
            return 100.0

        # Find previous threshold to calculate progress
        lower_threshold = 0
        for t in sorted(self.thresholds):
            if t < self.next_threshold:
                lower_threshold = t

        threshold_range = self.next_threshold - lower_threshold
        current_progress = self.current_value - lower_threshold

        return (current_progress / threshold_range) * 100 if threshold_range > 0 else 0.0

    def should_use_screenshot_mode(self) -> bool:
        """Determine if operator should use screenshot mode.

        Returns:
            True if should use screenshot mode based on proximity.
        """
        if self.mode == OperatorMode.SCREENSHOT_ONLY:
            return True

        proximity = self.calculate_proximity()
        return proximity >= self.threshold_proximity_percent

    def update_mode(self) -> None:
        """Update operational mode based on current state."""
        if self.mode == OperatorMode.SCREENSHOT_ONLY:
            return  # Don't change if forced to screenshot only

        should_screenshot = self.should_use_screenshot_mode()

        if should_screenshot and self.mode != OperatorMode.SCREENSHOT:
            self.mode = OperatorMode.SCREENSHOT
            self.check_interval = self.screenshot_mode_interval
        elif not should_screenshot and self.mode != OperatorMode.API:
            self.mode = OperatorMode.API
            self.check_interval = self.api_mode_interval

    def update_value(self, new_value: int) -> bool:
        """Update current metric value and check for threshold crossing.

        Args:
            new_value: New metric value.

        Returns:
            True if a threshold was crossed.
        """
        old_value = self.current_value
        self.current_value = new_value
        self.last_check = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        # Check if threshold was crossed
        if self.next_threshold and old_value and new_value >= self.next_threshold:
            self.milestone_reached = True
            return True

        return False

    def advance_to_next_threshold(self) -> None:
        """Move to the next threshold after current one is reached."""
        if not self.next_threshold:
            return

        # Find next threshold after current
        remaining = [t for t in sorted(self.thresholds) if t > self.next_threshold]

        if remaining:
            self.next_threshold = remaining[0]
            self.milestone_reached = False
        else:
            # All thresholds reached
            self.next_threshold = None

    def increment_api_calls(self) -> None:
        """Increment API call counter."""
        self.api_calls_made += 1
        self.total_checks += 1
        self.updated_at = datetime.now(timezone.utc)

    def increment_screenshots(self) -> None:
        """Increment screenshot counter."""
        self.screenshots_taken += 1
        self.total_checks += 1
        self.updated_at = datetime.now(timezone.utc)

    def increment_llm_calls(self) -> None:
        """Increment LLM call counter."""
        self.llm_calls_made += 1
        self.updated_at = datetime.now(timezone.utc)

    def get_cost_estimate(self) -> dict[str, float]:
        """Estimate costs based on usage.

        Returns:
            Dictionary with cost breakdown.
        """
        # Rough estimates (adjust based on actual pricing)
        api_cost = 0.0  # Most platform APIs are free
        screenshot_cost = self.screenshots_taken * 0.05  # Steel.dev estimate
        llm_cost = self.llm_calls_made * 0.01  # Vision API estimate

        return {
            "api_calls": api_cost,
            "screenshots": screenshot_cost,
            "llm_vision": llm_cost,
            "total": api_cost + screenshot_cost + llm_cost,
        }

    def get_summary(self) -> str:
        """Get human-readable summary of state.

        Returns:
            Formatted summary string.
        """
        proximity = self.calculate_proximity()
        return (
            f"{self.run_id}: {self.current_value or 'Unknown'}/{self.next_threshold} "
            f"({proximity:.1f}% proximity) - Mode: {self.mode.value} - "
            f"Checks: {self.total_checks} (API: {self.api_calls_made}, "
            f"Screenshots: {self.screenshots_taken})"
        )

    def __str__(self) -> str:
        """String representation."""
        return self.get_summary()
