# FABO Operators Guide

## Overview

Operators are the platform-specific integrations that handle communication with social media APIs and determine when milestones are reached. Each operator implements the `BaseOperator` interface and provides platform-specific logic.

## Operator Architecture

```
BaseOperator (Abstract)
├── GitHubOperator
├── TwitterOperator
├── LinkedInOperator
└── [Your Custom Operator]
```

## Available Operators

### GitHub Operator

**File**: `src/fabo/infrastructure/operators/github_operator.py`

**Tracked Metrics**:
- Stars (`MilestoneType.GITHUB_STARS`)
- Forks (`MilestoneType.GITHUB_FORKS`)
- Watchers (`MilestoneType.GITHUB_WATCHERS`)
- Open Issues (`MilestoneType.GITHUB_ISSUES`)

**Configuration**:

```yaml
platforms:
  github:
    enabled: true
    repositories:
      - owner: nkkko
        name: fabo
    milestone_thresholds:
      stars: [10, 50, 100, 500, 1000, 5000, 10000]
      forks: [10, 50, 100, 500, 1000]
    check_interval: 3600
```

**Environment Variables**:
```bash
GITHUB_TOKEN=your-github-personal-access-token
```

**API Documentation**: https://docs.github.com/en/rest

### Twitter/X Operator

**File**: `src/fabo/infrastructure/operators/twitter_operator.py`

**Tracked Metrics**:
- Followers (`MilestoneType.TWITTER_FOLLOWERS`)
- Tweet Count (`MilestoneType.TWITTER_TWEETS`)

**Configuration**:

```yaml
platforms:
  twitter:
    enabled: true
    username: your_twitter_username
    milestone_thresholds:
      followers: [100, 500, 1000, 5000, 10000]
      tweets: [100, 500, 1000, 5000]
    check_interval: 3600
```

**Environment Variables**:
```bash
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
```

**API Documentation**: https://developer.twitter.com/en/docs/twitter-api

### LinkedIn Operator

**File**: `src/fabo/infrastructure/operators/linkedin_operator.py`

**Status**: ⚠️ Limited due to API restrictions

**Note**: LinkedIn's API has strict access requirements. Full implementation requires OAuth 2.0 and partner status. Current implementation provides URL generation for screenshot-based tracking.

**Tracked Metrics**:
- Connections (`MilestoneType.LINKEDIN_CONNECTIONS`)
- Followers (`MilestoneType.LINKEDIN_FOLLOWERS`)

**Configuration**:

```yaml
platforms:
  linkedin:
    enabled: false
    profile_url: https://www.linkedin.com/in/your-profile
    milestone_thresholds:
      connections: [100, 500, 1000, 5000]
    check_interval: 7200
```

## Creating a Custom Operator

Want to add support for a new platform? Here's how:

### 1. Create Operator Class

```python
# src/fabo/infrastructure/operators/youtube_operator.py
from fabo.infrastructure.operators.base_operator import BaseOperator
from fabo.domain.value_objects.milestone_type import MilestoneType
from fabo.domain.entities.milestone import Milestone
import httpx

class YouTubeOperator(BaseOperator):
    """Operator for YouTube platform."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    async def validate_credentials(self) -> bool:
        """Validate YouTube API credentials."""
        # Implementation here
        pass

    async def get_current_stats(self) -> dict[MilestoneType, int]:
        """Get current YouTube channel statistics."""
        # Implementation here
        # Return something like:
        # {
        #     MilestoneType.YOUTUBE_SUBSCRIBERS: 1000,
        #     MilestoneType.YOUTUBE_VIEWS: 50000,
        # }
        pass

    def get_screenshot_url(self, milestone: Milestone) -> str:
        """Get the URL to screenshot."""
        channel_id = self.platform_config.target_config.get("channel_id")
        return f"https://www.youtube.com/channel/{channel_id}"
```

### 2. Add Milestone Types

```python
# src/fabo/domain/value_objects/milestone_type.py

class MilestoneType(str, Enum):
    # ... existing types ...

    # YouTube milestones
    YOUTUBE_SUBSCRIBERS = "youtube_subscribers"
    YOUTUBE_VIEWS = "youtube_views"
    YOUTUBE_VIDEOS = "youtube_videos"
```

### 3. Register Operator

Create an operator factory to map platform types to operators:

```python
# src/fabo/infrastructure/operators/factory.py
from fabo.domain.value_objects.milestone_type import PlatformType
from fabo.infrastructure.operators.base_operator import BaseOperator
from fabo.infrastructure.operators.github_operator import GitHubOperator
from fabo.infrastructure.operators.twitter_operator import TwitterOperator
from fabo.infrastructure.operators.youtube_operator import YouTubeOperator

def create_operator(platform_config) -> BaseOperator:
    """Factory function to create operators."""
    operators = {
        PlatformType.GITHUB: GitHubOperator,
        PlatformType.TWITTER: TwitterOperator,
        PlatformType.YOUTUBE: YouTubeOperator,
    }

    operator_class = operators.get(platform_config.platform_type)
    if not operator_class:
        raise ValueError(f"No operator for platform: {platform_config.platform_type}")

    return operator_class(platform_config)
```

### 4. Add Configuration

```yaml
# config.yaml
platforms:
  youtube:
    enabled: true
    channel_id: your-channel-id
    milestone_thresholds:
      subscribers: [100, 1000, 10000, 100000, 1000000]
      views: [10000, 100000, 1000000]
    check_interval: 3600
```

## Operator Lifecycle

1. **Initialization**: Operator is created with platform configuration
2. **Credential Validation**: `validate_credentials()` is called
3. **Periodic Checks**: `check_milestones()` is called at configured intervals
4. **Stats Retrieval**: `get_current_stats()` fetches current metrics
5. **Threshold Comparison**: Compares current vs. last known values
6. **Milestone Creation**: Creates `Milestone` entities for crossed thresholds
7. **Screenshot Capture**: `get_screenshot_url()` provides URL for capture

## Error Handling

Operators should handle three types of errors:

- **AuthenticationError**: Invalid credentials
- **RateLimitError**: API rate limit exceeded
- **PlatformAPIError**: Other API errors

Example:

```python
async def get_current_stats(self) -> dict[MilestoneType, int]:
    try:
        response = await client.get("/endpoint")

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")

        response.raise_for_status()
        return self._parse_stats(response.json())

    except httpx.HTTPStatusError as e:
        raise PlatformAPIError(f"API error: {e}") from e
```

## Best Practices

1. **Use Async/Await**: All I/O operations should be async
2. **Implement Context Managers**: Use `__aenter__` and `__aexit__` for cleanup
3. **Log Extensively**: Use structured logging for debugging
4. **Handle Rate Limits**: Respect API rate limits and implement backoff
5. **Cache When Possible**: Cache API responses if appropriate
6. **Type Hints**: Use full type hints for all methods
7. **Documentation**: Document all methods with docstrings

## Testing Operators

```python
# tests/unit/test_operators.py
import pytest
from fabo.infrastructure.operators.github_operator import GitHubOperator

@pytest.mark.asyncio
async def test_github_operator_validation():
    # Create platform config
    platform_config = create_test_platform_config()

    # Create operator
    operator = GitHubOperator(platform_config)

    # Test validation
    is_valid = await operator.validate_credentials()
    assert is_valid is True

    # Cleanup
    await operator.close()
```

## Troubleshooting

### API Authentication Fails

- Check that environment variables are set correctly
- Verify API token has required scopes/permissions
- Check token hasn't expired

### Rate Limiting

- Reduce check frequency in configuration
- Use authenticated requests (higher rate limits)
- Implement caching to reduce API calls

### Incorrect Stats

- Verify target configuration (repo owner/name, username, etc.)
- Check API response format hasn't changed
- Enable debug logging to see raw API responses

## Resources

- [BaseOperator Source](../src/fabo/infrastructure/operators/base_operator.py)
- [GitHub Operator Example](../src/fabo/infrastructure/operators/github_operator.py)
- [Domain Models](../src/fabo/domain/)
