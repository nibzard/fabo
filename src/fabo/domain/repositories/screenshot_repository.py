"""Screenshot repository interface.

This module defines the repository interface for screenshot persistence.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from fabo.domain.entities.screenshot import Screenshot


class ScreenshotRepository(ABC):
    """Abstract repository interface for screenshot persistence.

    This interface defines the contract for storing and retrieving screenshots.
    """

    @abstractmethod
    async def save(self, screenshot: Screenshot) -> Screenshot:
        """Save a screenshot to the repository.

        Args:
            screenshot: The screenshot to save.

        Returns:
            The saved screenshot.
        """
        pass

    @abstractmethod
    async def find_by_id(self, screenshot_id: UUID) -> Screenshot | None:
        """Find a screenshot by its ID.

        Args:
            screenshot_id: The unique identifier.

        Returns:
            The screenshot if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_milestone_id(self, milestone_id: UUID) -> Screenshot | None:
        """Find the screenshot associated with a milestone.

        Args:
            milestone_id: The milestone ID.

        Returns:
            The screenshot if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> list[Screenshot]:
        """Find all screenshots with pagination.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of screenshots.
        """
        pass

    @abstractmethod
    async def update(self, screenshot: Screenshot) -> Screenshot:
        """Update an existing screenshot.

        Args:
            screenshot: The screenshot with updated values.

        Returns:
            The updated screenshot.
        """
        pass

    @abstractmethod
    async def delete(self, screenshot_id: UUID) -> bool:
        """Delete a screenshot by ID.

        Args:
            screenshot_id: The ID of the screenshot to delete.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def get_total_size_bytes(self) -> int:
        """Get the total size of all screenshots in bytes.

        Returns:
            Total size in bytes.
        """
        pass

    @abstractmethod
    async def cleanup_orphaned_files(self, screenshots_dir: Path) -> int:
        """Clean up screenshot files that aren't tracked in the repository.

        Args:
            screenshots_dir: The directory containing screenshots.

        Returns:
            Number of files deleted.
        """
        pass
