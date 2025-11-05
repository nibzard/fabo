"""Twitter/X operator implementation.

This module provides the Twitter-specific implementation for checking milestones
and retrieving user statistics.

Note: Twitter API v2 requires authentication and has strict rate limits.
"""

import httpx

from fabo.domain.entities.milestone import Milestone
from fabo.domain.value_objects.milestone_type import MilestoneType
from fabo.infrastructure.operators.base_operator import (
    AuthenticationError,
    BaseOperator,
    PlatformAPIError,
    RateLimitError,
)


class TwitterOperator(BaseOperator):
    """Operator for Twitter/X platform.

    Tracks Twitter user statistics including:
    - Followers count
    - Tweet count
    - Following count

    Requires Twitter API v2 Bearer Token.
    """

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, *args, **kwargs):
        """Initialize Twitter operator."""
        super().__init__(*args, **kwargs)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication.

        Returns:
            Configured HTTP client.

        Raises:
            AuthenticationError: If bearer token is not configured.
        """
        if self._client is None:
            bearer_token = self.platform_config.credentials.get_bearer_token()
            if not bearer_token:
                raise AuthenticationError("Twitter Bearer Token not configured")

            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json",
            }

            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=headers,
                timeout=30.0,
            )

        return self._client

    async def validate_credentials(self) -> bool:
        """Validate Twitter credentials.

        Returns:
            True if credentials are valid.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        client = await self._get_client()

        try:
            # Try to get authenticated user info
            response = await client.get("/users/me")

            if response.status_code == 401:
                raise AuthenticationError("Invalid Twitter Bearer Token")

            if response.status_code == 429:
                raise RateLimitError("Twitter API rate limit exceeded")

            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid Twitter Bearer Token") from e
            if e.response.status_code == 429:
                raise RateLimitError("Twitter API rate limit exceeded") from e
            raise PlatformAPIError(f"Twitter API error: {e}") from e
        except httpx.RequestError as e:
            raise PlatformAPIError(f"Twitter API request failed: {e}") from e

    async def get_current_stats(self) -> dict[MilestoneType, int]:
        """Get current Twitter user statistics.

        Returns:
            Dictionary of milestone types to current values.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
            PlatformAPIError: If the API request fails.
        """
        client = await self._get_client()

        # Get username from target config
        username = self.platform_config.target_config.get("username")

        if not username:
            raise PlatformAPIError(
                "Missing required configuration: 'username' must be set in target_config"
            )

        try:
            # First, get user ID from username
            user_response = await client.get(
                f"/users/by/username/{username}",
                params={
                    "user.fields": "public_metrics",
                },
            )

            if user_response.status_code == 429:
                raise RateLimitError("Twitter API rate limit exceeded")

            if user_response.status_code == 401:
                raise AuthenticationError("Invalid Twitter Bearer Token")

            if user_response.status_code == 404:
                raise PlatformAPIError(f"Twitter user not found: {username}")

            user_response.raise_for_status()
            user_data = user_response.json()

            if "data" not in user_data:
                raise PlatformAPIError(f"Unexpected Twitter API response: {user_data}")

            # Extract public metrics
            public_metrics = user_data["data"].get("public_metrics", {})

            stats = {
                MilestoneType.TWITTER_FOLLOWERS: public_metrics.get("followers_count", 0),
                MilestoneType.TWITTER_TWEETS: public_metrics.get("tweet_count", 0),
            }

            self.logger.info(
                "twitter_stats_fetched",
                username=username,
                followers=stats[MilestoneType.TWITTER_FOLLOWERS],
                tweets=stats[MilestoneType.TWITTER_TWEETS],
            )

            return stats

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PlatformAPIError(f"Twitter user not found: {username}") from e
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid Twitter Bearer Token") from e
            if e.response.status_code == 429:
                raise RateLimitError("Twitter API rate limit exceeded") from e
            raise PlatformAPIError(f"Twitter API error: {e}") from e
        except httpx.RequestError as e:
            raise PlatformAPIError(f"Twitter API request failed: {e}") from e

    def get_screenshot_url(self, milestone: Milestone) -> str:
        """Get the URL to screenshot for a Twitter milestone.

        Args:
            milestone: The milestone that was reached.

        Returns:
            The Twitter profile URL.
        """
        username = self.platform_config.target_config.get("username")

        if not username:
            raise PlatformAPIError("Missing username configuration")

        return f"https://twitter.com/{username}"

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
