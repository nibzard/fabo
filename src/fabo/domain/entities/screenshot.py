"""Screenshot domain entity.

This module defines the Screenshot entity which represents a captured
screenshot of a milestone event.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class Screenshot(BaseModel):
    """Represents a captured screenshot of a milestone.

    Screenshots are captured using Steel.dev's browser API and stored
    locally or in cloud storage.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique screenshot identifier")
    milestone_id: UUID = Field(..., description="ID of the associated milestone")
    url: HttpUrl = Field(..., description="URL that was screenshotted")
    file_path: Path = Field(..., description="Local file path where screenshot is stored")
    captured_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the screenshot was captured",
    )
    file_size_bytes: int = Field(0, ge=0, description="Size of the screenshot file")
    format: str = Field("png", description="Image format (png, jpg, etc.)")
    width: int = Field(1920, gt=0, description="Screenshot width in pixels")
    height: int = Field(1080, gt=0, description="Screenshot height in pixels")
    full_page: bool = Field(True, description="Whether full page was captured")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (Steel session ID, etc.)",
    )
    cloud_url: str | None = Field(None, description="Cloud storage URL if uploaded")

    class Config:
        """Pydantic model configuration."""

        frozen = False  # Allow updates for file_size_bytes, cloud_url

    def exists(self) -> bool:
        """Check if the screenshot file exists on disk.

        Returns:
            True if the file exists.
        """
        return self.file_path.exists()

    def get_size_mb(self) -> float:
        """Get the file size in megabytes.

        Returns:
            File size in MB.
        """
        return self.file_size_bytes / (1024 * 1024)

    def update_file_size(self) -> None:
        """Update the file size from the actual file on disk."""
        if self.file_path.exists():
            object.__setattr__(self, "file_size_bytes", self.file_path.stat().st_size)

    def set_cloud_url(self, url: str) -> None:
        """Set the cloud storage URL after upload.

        Args:
            url: The cloud storage URL.
        """
        object.__setattr__(self, "cloud_url", url)

    def get_display_name(self) -> str:
        """Get a human-readable display name for the screenshot.

        Returns:
            A formatted filename.
        """
        timestamp = self.captured_at.strftime("%Y%m%d_%H%M%S")
        return f"screenshot_{timestamp}_{self.id}.{self.format}"

    def __str__(self) -> str:
        """Return string representation of the screenshot."""
        return f"Screenshot({self.id}) of {self.url} - {self.get_size_mb():.2f}MB"
