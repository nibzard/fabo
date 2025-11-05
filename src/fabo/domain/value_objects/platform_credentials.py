"""Platform credentials value object.

This module provides secure credential storage for platform integrations.
"""

from typing import Any

from pydantic import BaseModel, Field, SecretStr


class PlatformCredentials(BaseModel):
    """Secure credential storage for platform API access.

    Credentials are stored as SecretStr to prevent accidental logging
    or serialization of sensitive data.
    """

    platform: str = Field(..., description="Platform name (e.g., 'github', 'twitter')")
    api_key: SecretStr | None = Field(None, description="API key or access token")
    api_secret: SecretStr | None = Field(None, description="API secret (if required)")
    bearer_token: SecretStr | None = Field(None, description="Bearer token (if required)")
    additional_config: dict[str, Any] = Field(
        default_factory=dict, description="Additional platform-specific configuration"
    )

    class Config:
        """Pydantic model configuration."""

        frozen = True  # Make immutable (value object characteristic)

    def get_api_key(self) -> str | None:
        """Get the API key as a plain string.

        Returns:
            The API key or None if not set.
        """
        return self.api_key.get_secret_value() if self.api_key else None

    def get_api_secret(self) -> str | None:
        """Get the API secret as a plain string.

        Returns:
            The API secret or None if not set.
        """
        return self.api_secret.get_secret_value() if self.api_secret else None

    def get_bearer_token(self) -> str | None:
        """Get the bearer token as a plain string.

        Returns:
            The bearer token or None if not set.
        """
        return self.bearer_token.get_secret_value() if self.bearer_token else None

    def has_credentials(self) -> bool:
        """Check if any credentials are configured.

        Returns:
            True if at least one credential is set.
        """
        return any([self.api_key, self.api_secret, self.bearer_token])
