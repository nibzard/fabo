"""Smart operator with dual-mode operation (API + Screenshot with LLM).

This module extends the base operator to support intelligent mode switching
between API polling and screenshot-based validation.
"""

from pathlib import Path
from typing import Any

import structlog

from fabo.domain.entities.milestone import Milestone
from fabo.domain.entities.operator_state import OperatorMode, OperatorState
from fabo.domain.entities.run_config import RunConfig
from fabo.domain.entities.screenshot import Screenshot
from fabo.domain.value_objects.milestone_type import MilestoneType
from fabo.infrastructure.llm.vision_service import MetricExtraction, VisionService
from fabo.infrastructure.operators.base_operator import (
    BaseOperator,
    OperatorError,
    RateLimitError,
)
from fabo.infrastructure.screenshot.screenshot_service import ScreenshotService

logger = structlog.get_logger(__name__)


class SmartOperator:
    """Intelligent operator with API and screenshot modes.

    This operator implements the optimization strategy:
    - Use API when far from threshold (cost effective)
    - Switch to screenshots when approaching threshold (accurate)
    - Use LLM to extract metrics from screenshots
    - Validate and capture exact milestone moment
    """

    def __init__(
        self,
        base_operator: BaseOperator,
        run_config: RunConfig,
        state: OperatorState,
        screenshot_service: ScreenshotService,
        vision_service: VisionService,
    ):
        """Initialize smart operator.

        Args:
            base_operator: Platform-specific base operator.
            run_config: Run configuration.
            state: Current operator state.
            screenshot_service: Screenshot capture service.
            vision_service: LLM vision service for metric extraction.
        """
        self.base_operator = base_operator
        self.run_config = run_config
        self.state = state
        self.screenshot_service = screenshot_service
        self.vision_service = vision_service
        self.logger = logger.bind(
            run_id=state.run_id,
            platform=state.platform,
            mode=state.mode.value,
        )

    async def execute_check(self) -> dict[str, Any]:
        """Execute a milestone check using appropriate mode.

        Returns:
            Dictionary with check results including:
            - mode_used: Which mode was used
            - current_value: Current metric value
            - milestone_reached: Whether threshold was crossed
            - screenshot_path: Path to screenshot if taken
            - confidence: Confidence score if LLM was used
        """
        self.logger.info("executing_check", mode=self.state.mode.value)

        # Update mode based on proximity
        self.state.update_mode()

        result: dict[str, Any] = {
            "run_id": self.state.run_id,
            "mode_used": self.state.mode.value,
            "current_value": None,
            "milestone_reached": False,
            "screenshot_path": None,
            "confidence": None,
            "error": None,
        }

        try:
            if self.state.mode == OperatorMode.SCREENSHOT_ONLY:
                # Pure screenshot mode (no API)
                return await self._check_via_screenshot(result)

            elif self.state.mode == OperatorMode.SCREENSHOT:
                # Screenshot mode (near threshold)
                return await self._check_via_screenshot(result)

            elif self.state.mode == OperatorMode.API:
                # API mode (far from threshold)
                return await self._check_via_api(result)

            elif self.state.mode == OperatorMode.HYBRID:
                # Both API and screenshot for validation
                return await self._check_hybrid(result)

        except RateLimitError as e:
            self.logger.warning("rate_limit_hit", error=str(e))
            result["error"] = f"Rate limit: {e}"
            # Fall back to screenshot mode
            return await self._check_via_screenshot(result)

        except Exception as e:
            self.logger.error("check_failed", error=str(e))
            result["error"] = str(e)
            return result

        return result

    async def _check_via_api(self, result: dict[str, Any]) -> dict[str, Any]:
        """Check using platform API.

        Args:
            result: Result dictionary to populate.

        Returns:
            Updated result dictionary.
        """
        self.logger.info("checking_via_api")

        try:
            # Get current stats from API
            stats = await self.base_operator.get_current_stats()

            # Extract primary metric
            metric_type = self._get_metric_type()
            current_value = stats.get(metric_type)

            if current_value is not None:
                result["current_value"] = current_value
                self.state.increment_api_calls()

                # Check for threshold crossing
                threshold_crossed = self.state.update_value(current_value)

                if threshold_crossed:
                    self.logger.info(
                        "milestone_detected_api",
                        value=current_value,
                        threshold=self.state.next_threshold,
                    )
                    result["milestone_reached"] = True

                    # Take screenshot to commemorate
                    milestone = await self._create_milestone(current_value)
                    screenshot = await self._capture_screenshot(milestone)
                    result["screenshot_path"] = str(screenshot.file_path)

            return result

        except Exception as e:
            self.logger.error("api_check_failed", error=str(e))
            result["error"] = str(e)
            raise

    async def _check_via_screenshot(self, result: dict[str, Any]) -> dict[str, Any]:
        """Check using screenshot + LLM extraction.

        Args:
            result: Result dictionary to populate.

        Returns:
            Updated result dictionary.
        """
        self.logger.info("checking_via_screenshot")

        try:
            # Get URL to screenshot
            milestone = await self._create_milestone(0)  # Temporary milestone
            url = self.base_operator.get_screenshot_url(milestone)

            # Capture screenshot
            screenshot_path = Path("temp_screenshots") / f"{self.state.run_id}_check.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            await self.screenshot_service.steel_client.capture_screenshot(
                url=url,
                output_path=screenshot_path,
                full_page=True,
            )

            self.state.increment_screenshots()

            # Extract metric using LLM
            extraction = await self._extract_metric_from_screenshot(screenshot_path)

            self.state.increment_llm_calls()

            # Check confidence
            min_confidence = self.run_config.optimization.min_confidence
            if extraction.confidence < min_confidence:
                self.logger.warning(
                    "low_confidence_extraction",
                    confidence=extraction.confidence,
                    min_required=min_confidence,
                )
                # Could retry here
                result["confidence"] = extraction.confidence
                result["error"] = f"Low confidence: {extraction.confidence}"
                return result

            # Update state with extracted value
            if extraction.metric_value is not None:
                result["current_value"] = extraction.metric_value
                result["confidence"] = extraction.confidence

                threshold_crossed = self.state.update_value(extraction.metric_value)

                if threshold_crossed:
                    self.logger.info(
                        "milestone_detected_screenshot",
                        value=extraction.metric_value,
                        threshold=self.state.next_threshold,
                    )
                    result["milestone_reached"] = True

                    # Keep this screenshot as the milestone capture
                    final_path = (
                        Path("screenshots")
                        / f"{self.state.run_id}_{self.state.next_threshold}.png"
                    )
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    screenshot_path.rename(final_path)
                    result["screenshot_path"] = str(final_path)

            return result

        except Exception as e:
            self.logger.error("screenshot_check_failed", error=str(e))
            result["error"] = str(e)
            raise

    async def _check_hybrid(self, result: dict[str, Any]) -> dict[str, Any]:
        """Check using both API and screenshot for validation.

        Args:
            result: Result dictionary to populate.

        Returns:
            Updated result dictionary.
        """
        self.logger.info("checking_hybrid")

        # First try API
        api_result = await self._check_via_api(result.copy())

        # Then validate with screenshot
        screenshot_result = await self._check_via_screenshot(result.copy())

        # Compare results
        if api_result.get("current_value") and screenshot_result.get("current_value"):
            api_value = api_result["current_value"]
            screenshot_value = screenshot_result["current_value"]

            # Check if they match (allow small difference)
            if abs(api_value - screenshot_value) <= 5:
                result["current_value"] = screenshot_value
                result["confidence"] = screenshot_result.get("confidence", 1.0)
                result["validated"] = True
            else:
                self.logger.warning(
                    "api_screenshot_mismatch",
                    api_value=api_value,
                    screenshot_value=screenshot_value,
                )
                # Trust screenshot more
                result["current_value"] = screenshot_value
                result["confidence"] = screenshot_result.get("confidence", 0.5)

        return result

    async def _extract_metric_from_screenshot(
        self, screenshot_path: Path
    ) -> MetricExtraction:
        """Extract metric from screenshot using LLM.

        Args:
            screenshot_path: Path to screenshot.

        Returns:
            Metric extraction result.
        """
        platform = self.state.platform.lower()

        if platform == "github":
            expected_repo = f"{self.state.target.get('owner')}/{self.state.target.get('repo')}"
            return await self.vision_service.analyze_github_screenshot(
                screenshot_path, expected_repo
            )
        elif platform == "twitter":
            expected_username = self.state.target.get("username")
            return await self.vision_service.analyze_twitter_screenshot(
                screenshot_path, expected_username
            )
        elif platform == "linkedin":
            return await self.vision_service.analyze_linkedin_screenshot(screenshot_path)
        else:
            raise OperatorError(f"Unsupported platform for LLM extraction: {platform}")

    def _get_metric_type(self) -> MilestoneType:
        """Get milestone type for primary metric.

        Returns:
            Milestone type enum.
        """
        from fabo.domain.value_objects.milestone_type import MilestoneType

        # Map metric name to milestone type
        metric_mappings = {
            "stars": MilestoneType.GITHUB_STARS,
            "forks": MilestoneType.GITHUB_FORKS,
            "watchers": MilestoneType.GITHUB_WATCHERS,
            "followers": MilestoneType.TWITTER_FOLLOWERS,
            "tweets": MilestoneType.TWITTER_TWEETS,
            "connections": MilestoneType.LINKEDIN_CONNECTIONS,
        }

        metric_name = self.state.metric_name.lower()
        return metric_mappings.get(
            metric_name, MilestoneType.GITHUB_STARS
        )  # Default to stars

    async def _create_milestone(self, current_value: int) -> Milestone:
        """Create a milestone entity.

        Args:
            current_value: Current metric value.

        Returns:
            Milestone entity.
        """
        from fabo.domain.value_objects.milestone_type import PlatformType

        platform_type = PlatformType(self.state.platform)
        milestone_type = self._get_metric_type()

        return Milestone(
            platform=platform_type,
            milestone_type=milestone_type,
            threshold_value=self.state.next_threshold or current_value,
            actual_value=current_value,
            metadata={
                "run_id": self.state.run_id,
                **self.state.target,
            },
        )

    async def _capture_screenshot(self, milestone: Milestone) -> Screenshot:
        """Capture and save screenshot for milestone.

        Args:
            milestone: Milestone entity.

        Returns:
            Screenshot entity.
        """
        url = self.base_operator.get_screenshot_url(milestone)
        return await self.screenshot_service.capture_milestone_screenshot(milestone, url)

    def get_state(self) -> OperatorState:
        """Get current operator state.

        Returns:
            Current state.
        """
        return self.state
