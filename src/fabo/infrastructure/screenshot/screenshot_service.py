"""Screenshot service for capturing milestone screenshots.

This module provides a high-level service for capturing and managing
screenshots using the Steel.dev client.
"""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import structlog

from fabo.domain.entities.milestone import Milestone
from fabo.domain.entities.screenshot import Screenshot
from fabo.infrastructure.screenshot.steel_client import SteelClient, SteelClientError

logger = structlog.get_logger(__name__)


class ScreenshotService:
    """High-level service for screenshot operations.

    This service handles:
    1. Screenshot capture using Steel.dev
    2. File management and storage
    3. Screenshot entity creation
    """

    def __init__(
        self,
        steel_client: SteelClient,
        screenshots_dir: Path,
        default_format: str = "png",
    ):
        """Initialize screenshot service.

        Args:
            steel_client: Steel.dev client instance.
            screenshots_dir: Directory to store screenshots.
            default_format: Default image format.
        """
        self.steel_client = steel_client
        self.screenshots_dir = Path(screenshots_dir)
        self.default_format = default_format
        self.logger = logger.bind(service="screenshot_service")

        # Ensure screenshots directory exists
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(
        self,
        milestone_id: UUID,
        timestamp: datetime | None = None,
    ) -> str:
        """Generate a unique filename for a screenshot.

        Args:
            milestone_id: The milestone ID.
            timestamp: The timestamp (defaults to now).

        Returns:
            Generated filename.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"milestone_{milestone_id}_{timestamp_str}.{self.default_format}"

    async def capture_milestone_screenshot(
        self,
        milestone: Milestone,
        url: str,
        full_page: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ) -> Screenshot:
        """Capture a screenshot for a milestone.

        Args:
            milestone: The milestone entity.
            url: The URL to screenshot.
            full_page: Whether to capture the full page.
            viewport_width: Browser viewport width.
            viewport_height: Browser viewport height.

        Returns:
            Screenshot entity.

        Raises:
            SteelClientError: If screenshot capture fails.
        """
        self.logger.info(
            "capturing_milestone_screenshot",
            milestone_id=str(milestone.id),
            url=url,
        )

        # Generate filename and path
        filename = self._generate_filename(milestone.id)
        file_path = self.screenshots_dir / filename

        try:
            # Capture screenshot using Steel client
            result = await self.steel_client.capture_screenshot(
                url=url,
                output_path=file_path,
                full_page=full_page,
                viewport_width=viewport_width,
                viewport_height=viewport_height,
            )

            # Create Screenshot entity
            screenshot = Screenshot(
                milestone_id=milestone.id,
                url=url,  # type: ignore
                file_path=file_path,
                file_size_bytes=result.get("file_size_bytes", 0),
                format=self.default_format,
                width=viewport_width,
                height=viewport_height,
                full_page=full_page,
                metadata={
                    "platform": milestone.platform.value,
                    "milestone_type": milestone.milestone_type.value,
                    "threshold": milestone.threshold_value,
                },
            )

            self.logger.info(
                "screenshot_captured_successfully",
                screenshot_id=str(screenshot.id),
                milestone_id=str(milestone.id),
                file_size_mb=screenshot.get_size_mb(),
            )

            return screenshot

        except SteelClientError as e:
            self.logger.error(
                "screenshot_capture_failed",
                milestone_id=str(milestone.id),
                url=url,
                error=str(e),
            )
            raise

    async def delete_screenshot(self, screenshot: Screenshot) -> bool:
        """Delete a screenshot file.

        Args:
            screenshot: The screenshot entity.

        Returns:
            True if deleted successfully.
        """
        try:
            if screenshot.file_path.exists():
                screenshot.file_path.unlink()
                self.logger.info(
                    "screenshot_deleted",
                    screenshot_id=str(screenshot.id),
                    file_path=str(screenshot.file_path),
                )
                return True
            else:
                self.logger.warning(
                    "screenshot_file_not_found",
                    screenshot_id=str(screenshot.id),
                    file_path=str(screenshot.file_path),
                )
                return False
        except Exception as e:
            self.logger.error(
                "screenshot_deletion_failed",
                screenshot_id=str(screenshot.id),
                error=str(e),
            )
            return False

    def get_total_storage_size(self) -> int:
        """Get total size of all screenshots in bytes.

        Returns:
            Total size in bytes.
        """
        total_size = 0
        for file_path in self.screenshots_dir.glob(f"*.{self.default_format}"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size

    def get_storage_size_mb(self) -> float:
        """Get total storage size in megabytes.

        Returns:
            Total size in MB.
        """
        return self.get_total_storage_size() / (1024 * 1024)

    async def cleanup_orphaned_files(self, tracked_screenshot_ids: set[UUID]) -> int:
        """Clean up screenshot files that aren't tracked.

        Args:
            tracked_screenshot_ids: Set of screenshot IDs that should exist.

        Returns:
            Number of files deleted.
        """
        deleted_count = 0

        for file_path in self.screenshots_dir.glob(f"*.{self.default_format}"):
            if not file_path.is_file():
                continue

            # Check if this file corresponds to a tracked screenshot
            # Files are named: milestone_{milestone_id}_{timestamp}.png
            # We can't directly map to screenshot ID, so we'll keep all files
            # This is a simplified version - in production, you'd want more
            # sophisticated tracking

            # For now, we'll just log orphaned files but not delete them
            # to avoid accidental data loss
            pass

        return deleted_count
