"""Milestone repository interface.

This module defines the repository interface for milestone persistence.
Following the Repository pattern from Domain-Driven Design.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from fabo.domain.entities.milestone import Milestone
from fabo.domain.value_objects.milestone_type import MilestoneType, PlatformType


class MilestoneRepository(ABC):
    """Abstract repository interface for milestone persistence.

    This interface defines the contract for storing and retrieving milestones.
    Concrete implementations can use different storage backends (SQLite, PostgreSQL, etc.).
    """

    @abstractmethod
    async def save(self, milestone: Milestone) -> Milestone:
        """Save a milestone to the repository.

        Args:
            milestone: The milestone to save.

        Returns:
            The saved milestone (with any generated IDs).
        """
        pass

    @abstractmethod
    async def find_by_id(self, milestone_id: UUID) -> Milestone | None:
        """Find a milestone by its ID.

        Args:
            milestone_id: The unique identifier of the milestone.

        Returns:
            The milestone if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_all(
        self,
        platform: PlatformType | None = None,
        milestone_type: MilestoneType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Milestone]:
        """Find all milestones with optional filtering.

        Args:
            platform: Filter by platform type (optional).
            milestone_type: Filter by milestone type (optional).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).

        Returns:
            List of milestones matching the criteria.
        """
        pass

    @abstractmethod
    async def find_by_platform_and_type(
        self, platform: PlatformType, milestone_type: MilestoneType
    ) -> list[Milestone]:
        """Find all milestones for a specific platform and type.

        Args:
            platform: The platform type.
            milestone_type: The milestone type.

        Returns:
            List of matching milestones.
        """
        pass

    @abstractmethod
    async def find_recent(self, hours: int = 24, limit: int = 100) -> list[Milestone]:
        """Find milestones detected within the last N hours.

        Args:
            hours: Number of hours to look back.
            limit: Maximum number of results.

        Returns:
            List of recent milestones.
        """
        pass

    @abstractmethod
    async def exists_for_threshold(
        self, platform: PlatformType, milestone_type: MilestoneType, threshold_value: int
    ) -> bool:
        """Check if a milestone already exists for a specific threshold.

        This prevents duplicate milestone creation.

        Args:
            platform: The platform type.
            milestone_type: The milestone type.
            threshold_value: The threshold value.

        Returns:
            True if a milestone exists for this threshold.
        """
        pass

    @abstractmethod
    async def update(self, milestone: Milestone) -> Milestone:
        """Update an existing milestone.

        Args:
            milestone: The milestone with updated values.

        Returns:
            The updated milestone.
        """
        pass

    @abstractmethod
    async def delete(self, milestone_id: UUID) -> bool:
        """Delete a milestone by ID.

        Args:
            milestone_id: The ID of the milestone to delete.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def count(
        self, platform: PlatformType | None = None, milestone_type: MilestoneType | None = None
    ) -> int:
        """Count milestones with optional filtering.

        Args:
            platform: Filter by platform (optional).
            milestone_type: Filter by milestone type (optional).

        Returns:
            Total count of matching milestones.
        """
        pass
