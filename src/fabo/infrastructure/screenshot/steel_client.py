"""Steel.dev client for browser automation and screenshots.

This module provides a client for interacting with Steel.dev's headless
browser API to capture screenshots of milestone pages.
"""

from pathlib import Path
from typing import Any

import httpx
import structlog
from pydantic import HttpUrl

logger = structlog.get_logger(__name__)


class SteelClientError(Exception):
    """Base exception for Steel client errors."""

    pass


class SteelAuthenticationError(SteelClientError):
    """Raised when Steel API authentication fails."""

    pass


class SteelSessionError(SteelClientError):
    """Raised when Steel session operations fail."""

    pass


class SteelScreenshotError(SteelClientError):
    """Raised when screenshot capture fails."""

    pass


class SteelClient:
    """Client for Steel.dev browser automation API.

    This client handles:
    1. Session creation and management
    2. Screenshot capture
    3. Browser automation via CDP
    """

    def __init__(self, api_key: str, base_url: str = "https://api.steel.dev/v1"):
        """Initialize Steel client.

        Args:
            api_key: Steel API key.
            base_url: Steel API base URL.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logger.bind(service="steel_client")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Configured HTTP client.
        """
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=60.0,  # Screenshots can take time
            )

        return self._client

    async def create_session(
        self,
        proxy: bool = False,
        solve_captcha: bool = False,
        session_timeout: int = 300000,
    ) -> dict[str, Any]:
        """Create a new Steel browser session.

        Args:
            proxy: Enable proxy for the session.
            solve_captcha: Enable automatic CAPTCHA solving.
            session_timeout: Session timeout in milliseconds.

        Returns:
            Session information including session ID and CDP URL.

        Raises:
            SteelAuthenticationError: If API key is invalid.
            SteelSessionError: If session creation fails.
        """
        client = await self._get_client()

        payload = {
            "useProxy": proxy,
            "solveCaptchas": solve_captcha,
            "sessionTimeout": session_timeout,
        }

        try:
            response = await client.post("/sessions", json=payload)

            if response.status_code == 401:
                raise SteelAuthenticationError("Invalid Steel API key")

            response.raise_for_status()
            session_data = response.json()

            self.logger.info(
                "steel_session_created",
                session_id=session_data.get("id"),
            )

            return session_data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise SteelAuthenticationError("Invalid Steel API key") from e
            raise SteelSessionError(f"Failed to create Steel session: {e}") from e
        except httpx.RequestError as e:
            raise SteelSessionError(f"Steel API request failed: {e}") from e

    async def capture_screenshot(
        self,
        url: str | HttpUrl,
        output_path: Path,
        full_page: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ) -> dict[str, Any]:
        """Capture a screenshot of a URL using Steel.dev.

        Args:
            url: The URL to screenshot.
            output_path: Where to save the screenshot.
            full_page: Whether to capture the full page.
            viewport_width: Browser viewport width.
            viewport_height: Browser viewport height.

        Returns:
            Screenshot metadata.

        Raises:
            SteelScreenshotError: If screenshot capture fails.
        """
        client = await self._get_client()

        # Convert URL to string if HttpUrl
        url_str = str(url)

        payload = {
            "url": url_str,
            "fullPage": full_page,
            "viewportWidth": viewport_width,
            "viewportHeight": viewport_height,
        }

        try:
            self.logger.info("capturing_screenshot", url=url_str)

            # Use the scrape endpoint with screenshot option
            response = await client.post("/scrape", json=payload)

            if response.status_code == 401:
                raise SteelAuthenticationError("Invalid Steel API key")

            response.raise_for_status()
            result = response.json()

            # The response should contain screenshot data
            # Note: Actual Steel API response format may vary
            # This is based on common patterns
            if "screenshot" in result:
                screenshot_data = result["screenshot"]

                # If screenshot is base64 encoded
                if isinstance(screenshot_data, str):
                    import base64

                    # Decode and save
                    screenshot_bytes = base64.b64decode(screenshot_data)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(screenshot_bytes)

                    self.logger.info(
                        "screenshot_saved",
                        url=url_str,
                        path=str(output_path),
                        size_bytes=len(screenshot_bytes),
                    )

                    return {
                        "success": True,
                        "url": url_str,
                        "file_path": str(output_path),
                        "file_size_bytes": len(screenshot_bytes),
                    }

            # Alternative: If Steel returns a URL to download
            elif "screenshotUrl" in result:
                screenshot_url = result["screenshotUrl"]

                # Download the screenshot
                download_response = await client.get(screenshot_url)
                download_response.raise_for_status()

                screenshot_bytes = download_response.content
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(screenshot_bytes)

                self.logger.info(
                    "screenshot_downloaded",
                    url=url_str,
                    path=str(output_path),
                    size_bytes=len(screenshot_bytes),
                )

                return {
                    "success": True,
                    "url": url_str,
                    "file_path": str(output_path),
                    "file_size_bytes": len(screenshot_bytes),
                }

            else:
                raise SteelScreenshotError(
                    f"Unexpected Steel API response format: {result.keys()}"
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise SteelAuthenticationError("Invalid Steel API key") from e
            raise SteelScreenshotError(f"Failed to capture screenshot: {e}") from e
        except httpx.RequestError as e:
            raise SteelScreenshotError(f"Steel API request failed: {e}") from e
        except Exception as e:
            raise SteelScreenshotError(f"Screenshot capture error: {e}") from e

    async def release_session(self, session_id: str) -> bool:
        """Release a Steel browser session.

        Args:
            session_id: The session ID to release.

        Returns:
            True if successful.
        """
        client = await self._get_client()

        try:
            response = await client.delete(f"/sessions/{session_id}")
            response.raise_for_status()

            self.logger.info("steel_session_released", session_id=session_id)
            return True

        except httpx.HTTPStatusError as e:
            self.logger.warning(
                "steel_session_release_failed",
                session_id=session_id,
                error=str(e),
            )
            return False
        except httpx.RequestError as e:
            self.logger.warning(
                "steel_session_release_request_failed",
                session_id=session_id,
                error=str(e),
            )
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
