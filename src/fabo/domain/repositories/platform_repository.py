"""Platform repository interface.

This module defines the repository interface for platform configuration persistence.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from fabo.domain.entities.platform import Platform
from fabo.domain.value_objects.milestone_type import PlatformType


class PlatformRepository(ABC):
    """Abstract repository interface for platform configuration persistence."""

    @abstractmethod
    async def save(self, platform: Platform) -> Platform:
        """Save a platform configuration.

        Args:
            platform: The platform configuration to save.

        Returns:
            The saved platform.
        """
        pass

    @abstractmethod
    async def find_by_id(self, platform_id: UUID) -> Platform | None:
        """Find a platform configuration by ID.

        Args:
            platform_id: The unique identifier.

        Returns:
            The platform if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_type(self, platform_type: PlatformType) -> list[Platform]:
        """Find all platform configurations of a specific type.

        Args:
            platform_type: The platform type.

        Returns:
            List of matching platforms.
        """
        pass

    @abstractmethod
    async def find_enabled(self) -> list[Platform]:
        """Find all enabled platform configurations.

        Returns:
            List of enabled platforms.
        """
        pass

    @abstractmethod
    async def find_all(self) -> list[Platform]:
        """Find all platform configurations.

        Returns:
            List of all platforms.
        """
        pass

    @abstractmethod
    async def update(self, platform: Platform) -> Platform:
        """Update a platform configuration.

        Args:
            platform: The platform with updated values.

        Returns:
            The updated platform.
        """
        pass

    @abstractmethod
    async def delete(self, platform_id: UUID) -> bool:
        """Delete a platform configuration.

        Args:
            platform_id: The ID of the platform to delete.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def exists(self, platform_id: UUID) -> bool:
        """Check if a platform configuration exists.

        Args:
            platform_id: The platform ID.

        Returns:
            True if exists, False otherwise.
        """
        pass
