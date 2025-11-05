"""Operator factory for creating platform-specific operators.

This module provides a factory function to instantiate the correct
operator based on platform type.
"""

from fabo.domain.entities.platform import Platform
from fabo.domain.value_objects.milestone_type import PlatformType
from fabo.infrastructure.operators.base_operator import BaseOperator
from fabo.infrastructure.operators.github_operator import GitHubOperator
from fabo.infrastructure.operators.linkedin_operator import LinkedInOperator
from fabo.infrastructure.operators.twitter_operator import TwitterOperator


class OperatorFactoryError(Exception):
    """Raised when operator creation fails."""

    pass


def create_operator(platform_config: Platform) -> BaseOperator:
    """Factory function to create platform-specific operators.

    Args:
        platform_config: Platform configuration entity.

    Returns:
        Appropriate operator instance for the platform.

    Raises:
        OperatorFactoryError: If no operator exists for the platform type.
    """
    # Map platform types to operator classes
    operators: dict[PlatformType, type[BaseOperator]] = {
        PlatformType.GITHUB: GitHubOperator,
        PlatformType.TWITTER: TwitterOperator,
        PlatformType.LINKEDIN: LinkedInOperator,
        # Add new operators here:
        # PlatformType.YOUTUBE: YouTubeOperator,
        # PlatformType.INSTAGRAM: InstagramOperator,
    }

    operator_class = operators.get(platform_config.platform_type)

    if operator_class is None:
        raise OperatorFactoryError(
            f"No operator implementation found for platform: {platform_config.platform_type.value}"
        )

    return operator_class(platform_config)


def get_supported_platforms() -> list[PlatformType]:
    """Get list of platforms that have operator implementations.

    Returns:
        List of supported platform types.
    """
    return [
        PlatformType.GITHUB,
        PlatformType.TWITTER,
        PlatformType.LINKEDIN,
    ]


def is_platform_supported(platform_type: PlatformType) -> bool:
    """Check if a platform type has an operator implementation.

    Args:
        platform_type: The platform type to check.

    Returns:
        True if the platform is supported.
    """
    return platform_type in get_supported_platforms()
