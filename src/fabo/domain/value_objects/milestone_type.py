"""Milestone type value object.

This module defines the different types of milestones that can be tracked
across various social media platforms.
"""

from enum import Enum


class PlatformType(str, Enum):
    """Supported social media platforms."""

    GITHUB = "github"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"


class MilestoneType(str, Enum):
    """Types of milestones that can be tracked.

    Each milestone type is prefixed with its platform to avoid naming conflicts.
    """

    # GitHub milestones
    GITHUB_STARS = "github_stars"
    GITHUB_FORKS = "github_forks"
    GITHUB_WATCHERS = "github_watchers"
    GITHUB_CONTRIBUTORS = "github_contributors"
    GITHUB_ISSUES = "github_issues"
    GITHUB_PULL_REQUESTS = "github_pull_requests"

    # Twitter/X milestones
    TWITTER_FOLLOWERS = "twitter_followers"
    TWITTER_TWEETS = "twitter_tweets"
    TWITTER_LIKES = "twitter_likes"

    # LinkedIn milestones
    LINKEDIN_CONNECTIONS = "linkedin_connections"
    LINKEDIN_FOLLOWERS = "linkedin_followers"
    LINKEDIN_POST_VIEWS = "linkedin_post_views"

    # YouTube milestones
    YOUTUBE_SUBSCRIBERS = "youtube_subscribers"
    YOUTUBE_VIEWS = "youtube_views"
    YOUTUBE_VIDEOS = "youtube_videos"

    # Instagram milestones
    INSTAGRAM_FOLLOWERS = "instagram_followers"
    INSTAGRAM_POSTS = "instagram_posts"
    INSTAGRAM_LIKES = "instagram_likes"

    @property
    def platform(self) -> PlatformType:
        """Get the platform this milestone type belongs to."""
        platform_name = self.value.split("_")[0]
        return PlatformType(platform_name)

    @property
    def metric_name(self) -> str:
        """Get the human-readable metric name."""
        parts = self.value.split("_")
        return " ".join(parts[1:]).title()

    def __str__(self) -> str:
        """Return a string representation."""
        return self.value
