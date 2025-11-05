"""GitHub operator implementation.

This module provides the GitHub-specific implementation for checking milestones
and retrieving repository statistics.
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


class GitHubOperator(BaseOperator):
    """Operator for GitHub platform.

    Tracks GitHub repository statistics including:
    - Stars
    - Forks
    - Watchers
    - Contributors
    - Open issues
    - Open pull requests
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, *args, **kwargs):
        """Initialize GitHub operator."""
        super().__init__(*args, **kwargs)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication.

        Returns:
            Configured HTTP client.
        """
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            # Add authentication if token is provided
            token = self.platform_config.credentials.get_api_key()
            if token:
                headers["Authorization"] = f"Bearer {token}"

            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=headers,
                timeout=30.0,
            )

        return self._client

    async def validate_credentials(self) -> bool:
        """Validate GitHub credentials by checking user authentication.

        Returns:
            True if credentials are valid.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        client = await self._get_client()

        try:
            response = await client.get("/user")

            if response.status_code == 401:
                raise AuthenticationError("Invalid GitHub token")

            if response.status_code == 403:
                # Check if it's rate limiting
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = int(response.headers["X-RateLimit-Remaining"])
                    if remaining == 0:
                        raise RateLimitError("GitHub API rate limit exceeded")
                raise AuthenticationError("GitHub API access forbidden")

            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid GitHub token") from e
            raise PlatformAPIError(f"GitHub API error: {e}") from e
        except httpx.RequestError as e:
            raise PlatformAPIError(f"GitHub API request failed: {e}") from e

    async def get_current_stats(self) -> dict[MilestoneType, int]:
        """Get current GitHub repository statistics.

        Returns:
            Dictionary of milestone types to current values.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
            PlatformAPIError: If the API request fails.
        """
        client = await self._get_client()

        # Get repository owner and name from target config
        owner = self.platform_config.target_config.get("owner")
        repo = self.platform_config.target_config.get("repo")

        if not owner or not repo:
            raise PlatformAPIError(
                "Missing required configuration: 'owner' and 'repo' must be set in target_config"
            )

        try:
            # Fetch repository data
            response = await client.get(f"/repos/{owner}/{repo}")

            # Check rate limiting
            if response.status_code == 403:
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = int(response.headers["X-RateLimit-Remaining"])
                    if remaining == 0:
                        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                        raise RateLimitError(
                            f"GitHub API rate limit exceeded. Resets at timestamp: {reset_time}"
                        )

            if response.status_code == 401:
                raise AuthenticationError("Invalid GitHub token")

            response.raise_for_status()
            data = response.json()

            # Extract statistics
            stats = {
                MilestoneType.GITHUB_STARS: data.get("stargazers_count", 0),
                MilestoneType.GITHUB_FORKS: data.get("forks_count", 0),
                MilestoneType.GITHUB_WATCHERS: data.get("watchers_count", 0),
            }

            # Optionally fetch additional stats (contributors, issues, PRs)
            # These require additional API calls, so we'll make them optional

            # Get open issues count
            stats[MilestoneType.GITHUB_ISSUES] = data.get("open_issues_count", 0)

            self.logger.info(
                "github_stats_fetched",
                owner=owner,
                repo=repo,
                stars=stats[MilestoneType.GITHUB_STARS],
                forks=stats[MilestoneType.GITHUB_FORKS],
            )

            return stats

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PlatformAPIError(
                    f"Repository not found: {owner}/{repo}. "
                    "Check that the owner and repo names are correct."
                ) from e
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid GitHub token") from e
            raise PlatformAPIError(f"GitHub API error: {e}") from e
        except httpx.RequestError as e:
            raise PlatformAPIError(f"GitHub API request failed: {e}") from e

    def get_screenshot_url(self, milestone: Milestone) -> str:
        """Get the URL to screenshot for a GitHub milestone.

        Args:
            milestone: The milestone that was reached.

        Returns:
            The GitHub repository URL.
        """
        owner = self.platform_config.target_config.get("owner")
        repo = self.platform_config.target_config.get("repo")

        if not owner or not repo:
            raise PlatformAPIError("Missing repository configuration")

        return f"https://github.com/{owner}/{repo}"

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
