"""Base operator interface for platform integrations.

This module defines the abstract base class that all platform operators must implement.
Using the Strategy pattern to allow different platform implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from fabo.domain.entities.milestone import Milestone
from fabo.domain.entities.platform import Platform
from fabo.domain.value_objects.milestone_type import MilestoneType

logger = structlog.get_logger(__name__)


class OperatorError(Exception):
    """Base exception for operator errors."""

    pass


class AuthenticationError(OperatorError):
    """Raised when authentication fails."""

    pass


class RateLimitError(OperatorError):
    """Raised when API rate limit is exceeded."""

    pass


class PlatformAPIError(OperatorError):
    """Raised when platform API returns an error."""

    pass


class BaseOperator(ABC):
    """Abstract base class for platform operators.

    Each operator is responsible for:
    1. Authenticating with the platform API
    2. Fetching current metric values
    3. Checking for milestone thresholds
    4. Providing URLs for screenshot capture
    """

    def __init__(self, platform_config: Platform):
        """Initialize the operator.

        Args:
            platform_config: The platform configuration entity.
        """
        self.platform_config = platform_config
        self.logger = logger.bind(
            platform=platform_config.platform_type.value,
            platform_id=str(platform_config.id),
        )

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate that the platform credentials are correct.

        Returns:
            True if credentials are valid.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        pass

    @abstractmethod
    async def get_current_stats(self) -> dict[MilestoneType, int]:
        """Get current statistics from the platform.

        Returns:
            Dictionary mapping milestone types to their current values.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
            PlatformAPIError: If the platform API returns an error.
        """
        pass

    @abstractmethod
    def get_screenshot_url(self, milestone: Milestone) -> str:
        """Get the URL to screenshot for a specific milestone.

        Args:
            milestone: The milestone that was reached.

        Returns:
            The URL to capture as a screenshot.
        """
        pass

    async def check_milestones(self) -> list[Milestone]:
        """Check for new milestones by comparing current stats with thresholds.

        This is a template method that can be overridden for custom logic,
        but provides a sensible default implementation.

        Returns:
            List of newly detected milestones.
        """
        self.logger.info("checking_milestones", platform=self.platform_config.name)

        try:
            # Get current statistics
            current_stats = await self.get_current_stats()

            milestones: list[Milestone] = []

            # Check each metric against configured thresholds
            for milestone_type, current_value in current_stats.items():
                # Get thresholds for this milestone type
                thresholds = self.platform_config.get_thresholds_for_type(milestone_type)
                if not thresholds:
                    continue

                # Get last known value
                last_value = self.platform_config.get_last_check_value(milestone_type)

                # Update last check value
                self.platform_config.update_last_check_value(milestone_type, current_value)

                # Check if any thresholds were crossed
                for threshold in sorted(thresholds):
                    if last_value < threshold <= current_value:
                        # Milestone reached!
                        milestone = Milestone(
                            platform=self.platform_config.platform_type,
                            milestone_type=milestone_type,
                            threshold_value=threshold,
                            actual_value=current_value,
                            screenshot_url=None,  # Will be set when creating screenshot
                            metadata={
                                "platform_config_id": str(self.platform_config.id),
                                "platform_name": self.platform_config.name,
                                **self.platform_config.target_config,
                            },
                        )
                        milestones.append(milestone)

                        self.logger.info(
                            "milestone_detected",
                            milestone_type=milestone_type.value,
                            threshold=threshold,
                            current_value=current_value,
                        )

            return milestones

        except RateLimitError:
            self.logger.warning(
                "rate_limit_exceeded", platform=self.platform_config.platform_type.value
            )
            raise
        except Exception as e:
            self.logger.error(
                "check_milestones_failed",
                error=str(e),
                platform=self.platform_config.platform_type.value,
            )
            raise PlatformAPIError(f"Failed to check milestones: {e}") from e

    def get_platform_name(self) -> str:
        """Get the platform name.

        Returns:
            Platform name.
        """
        return self.platform_config.platform_type.value

    def is_enabled(self) -> bool:
        """Check if the platform is enabled.

        Returns:
            True if enabled.
        """
        return self.platform_config.enabled

    async def test_connection(self) -> dict[str, Any]:
        """Test the connection to the platform.

        Returns:
            Dictionary with connection test results.
        """
        try:
            is_valid = await self.validate_credentials()
            stats = await self.get_current_stats()

            return {
                "success": True,
                "credentials_valid": is_valid,
                "stats_retrieved": len(stats) > 0,
                "platform": self.get_platform_name(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "platform": self.get_platform_name(),
            }
