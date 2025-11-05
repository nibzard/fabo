"""LLM Vision service for analyzing screenshots and extracting metrics.

This module provides multimodal LLM integration for validating screenshots
and extracting metric values using vision models like Claude 3.5 Sonnet.
"""

import base64
from pathlib import Path
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class MetricExtraction(BaseModel):
    """Extracted metric data from screenshot analysis."""

    metric_name: str = Field(..., description="Name of the metric (e.g., 'stars', 'followers')")
    metric_value: int | None = Field(None, description="Extracted metric value")
    repository: str | None = Field(None, description="Repository or account name if visible")
    timestamp_visible: bool = Field(False, description="Whether timestamp is visible in image")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    additional_data: dict[str, Any] = Field(
        default_factory=dict, description="Additional extracted data"
    )
    raw_response: str | None = Field(None, description="Raw LLM response for debugging")


class VisionServiceError(Exception):
    """Base exception for vision service errors."""

    pass


class VisionService:
    """Service for analyzing screenshots using multimodal LLMs.

    Supports multiple vision models:
    - Claude 3.5 Sonnet (Anthropic)
    - GPT-4 Vision (OpenAI)
    - Gemini Vision (Google)
    """

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: str | None = None,
        model: str | None = None,
    ):
        """Initialize vision service.

        Args:
            provider: LLM provider ('anthropic', 'openai', 'google').
            api_key: API key for the provider.
            model: Specific model to use (defaults to best available).
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.logger = logger.bind(service="vision_service", provider=self.provider)

        # Set default models
        if model is None:
            model_defaults = {
                "anthropic": "claude-3-5-sonnet-20241022",
                "openai": "gpt-4o",
                "google": "gemini-1.5-pro",
            }
            self.model = model_defaults.get(self.provider, "claude-3-5-sonnet-20241022")
        else:
            self.model = model

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for API calls."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    def _image_to_base64(self, image_path: Path) -> str:
        """Convert image file to base64 string.

        Args:
            image_path: Path to image file.

        Returns:
            Base64 encoded image string.
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def analyze_github_screenshot(
        self, screenshot_path: Path, expected_repo: str | None = None
    ) -> MetricExtraction:
        """Analyze a GitHub repository screenshot.

        Args:
            screenshot_path: Path to screenshot image.
            expected_repo: Expected repository name (for validation).

        Returns:
            Extracted metrics with confidence scores.

        Raises:
            VisionServiceError: If analysis fails.
        """
        prompt = f"""Analyze this GitHub repository page screenshot and extract the metrics.

Look for the following information:
1. Repository name (owner/repo)
2. Number of stars (look for the star icon ⭐)
3. Number of forks (look for the fork icon)
4. Number of watchers/watching
5. Any visible timestamp or last update time

{"Expected repository: " + expected_repo if expected_repo else ""}

Return your analysis in JSON format:
{{
  "metric_name": "stars",
  "metric_value": 1234,
  "repository": "owner/repo",
  "timestamp_visible": true,
  "confidence": 0.95,
  "additional_data": {{
    "forks": 56,
    "watchers": 78
  }}
}}

Important:
- If you cannot clearly read a metric, set it to null
- Confidence should reflect how certain you are about the main metric value
- Only return numeric values for metrics
"""

        return await self._analyze_screenshot(screenshot_path, prompt, "stars")

    async def analyze_twitter_screenshot(
        self, screenshot_path: Path, expected_username: str | None = None
    ) -> MetricExtraction:
        """Analyze a Twitter/X profile screenshot.

        Args:
            screenshot_path: Path to screenshot image.
            expected_username: Expected username (for validation).

        Returns:
            Extracted metrics with confidence scores.
        """
        prompt = f"""Analyze this Twitter/X profile screenshot and extract the metrics.

Look for:
1. Username (@username)
2. Follower count
3. Following count
4. Tweet/Post count

{"Expected username: " + expected_username if expected_username else ""}

Return in JSON format:
{{
  "metric_name": "followers",
  "metric_value": 5000,
  "repository": "@username",
  "timestamp_visible": false,
  "confidence": 0.95,
  "additional_data": {{
    "following": 123,
    "tweets": 456
  }}
}}
"""

        return await self._analyze_screenshot(screenshot_path, prompt, "followers")

    async def analyze_linkedin_screenshot(
        self, screenshot_path: Path
    ) -> MetricExtraction:
        """Analyze a LinkedIn profile screenshot.

        Args:
            screenshot_path: Path to screenshot image.

        Returns:
            Extracted metrics with confidence scores.
        """
        prompt = """Analyze this LinkedIn profile screenshot and extract the metrics.

Look for:
1. Profile name
2. Number of connections
3. Number of followers (if visible)

Return in JSON format:
{{
  "metric_name": "connections",
  "metric_value": 1000,
  "repository": "FirstName LastName",
  "timestamp_visible": false,
  "confidence": 0.90,
  "additional_data": {{
    "followers": 5000
  }}
}}
"""

        return await self._analyze_screenshot(screenshot_path, prompt, "connections")

    async def _analyze_screenshot(
        self, screenshot_path: Path, prompt: str, metric_name: str
    ) -> MetricExtraction:
        """Generic screenshot analysis using LLM vision.

        Args:
            screenshot_path: Path to screenshot.
            prompt: Analysis prompt.
            metric_name: Name of primary metric to extract.

        Returns:
            Extracted metrics.

        Raises:
            VisionServiceError: If analysis fails.
        """
        if not screenshot_path.exists():
            raise VisionServiceError(f"Screenshot not found: {screenshot_path}")

        self.logger.info("analyzing_screenshot", path=str(screenshot_path), model=self.model)

        try:
            if self.provider == "anthropic":
                return await self._analyze_with_anthropic(screenshot_path, prompt, metric_name)
            elif self.provider == "openai":
                return await self._analyze_with_openai(screenshot_path, prompt, metric_name)
            else:
                raise VisionServiceError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            self.logger.error("screenshot_analysis_failed", error=str(e))
            raise VisionServiceError(f"Failed to analyze screenshot: {e}") from e

    async def _analyze_with_anthropic(
        self, screenshot_path: Path, prompt: str, metric_name: str
    ) -> MetricExtraction:
        """Analyze using Claude vision models.

        Args:
            screenshot_path: Path to screenshot.
            prompt: Analysis prompt.
            metric_name: Primary metric name.

        Returns:
            Extracted metrics.
        """
        client = await self._get_client()

        # Read and encode image
        image_data = self._image_to_base64(screenshot_path)
        media_type = "image/png" if screenshot_path.suffix == ".png" else "image/jpeg"

        # Prepare request
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }

        # Make API call
        response = await client.post(
            "https://api.anthropic.com/v1/messages", headers=headers, json=payload
        )
        response.raise_for_status()

        result = response.json()
        content = result["content"][0]["text"]

        # Parse JSON from response
        import json

        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            extracted_data = json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                extracted_data = json.loads(json_match.group())
            else:
                raise VisionServiceError(f"Could not parse JSON from LLM response: {content}")

        # Create MetricExtraction object
        return MetricExtraction(
            metric_name=extracted_data.get("metric_name", metric_name),
            metric_value=extracted_data.get("metric_value"),
            repository=extracted_data.get("repository"),
            timestamp_visible=extracted_data.get("timestamp_visible", False),
            confidence=extracted_data.get("confidence", 0.8),
            additional_data=extracted_data.get("additional_data", {}),
            raw_response=content,
        )

    async def _analyze_with_openai(
        self, screenshot_path: Path, prompt: str, metric_name: str
    ) -> MetricExtraction:
        """Analyze using OpenAI GPT-4 Vision.

        Args:
            screenshot_path: Path to screenshot.
            prompt: Analysis prompt.
            metric_name: Primary metric name.

        Returns:
            Extracted metrics.
        """
        client = await self._get_client()

        # Read and encode image
        image_data = self._image_to_base64(screenshot_path)
        data_uri = f"data:image/png;base64,{image_data}"

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            "max_tokens": 1024,
        }

        response = await client.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON response (similar to Anthropic)
        import json
        import re

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()

        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            extracted_data = json.loads(json_match.group())
        else:
            raise VisionServiceError(f"Could not parse JSON from response: {content}")

        return MetricExtraction(
            metric_name=extracted_data.get("metric_name", metric_name),
            metric_value=extracted_data.get("metric_value"),
            repository=extracted_data.get("repository"),
            timestamp_visible=extracted_data.get("timestamp_visible", False),
            confidence=extracted_data.get("confidence", 0.8),
            additional_data=extracted_data.get("additional_data", {}),
            raw_response=content,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
