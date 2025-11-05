"""Velocity tracking for metric changes.

This module tracks the rate of change (velocity) and acceleration
of metrics to enable smarter optimization decisions.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class MetricSnapshot:
    """A snapshot of a metric at a point in time."""

    timestamp: datetime
    value: int

    def age_seconds(self) -> float:
        """Get age of this snapshot in seconds."""
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds()


@dataclass
class VelocityMetrics:
    """Calculated velocity and acceleration metrics."""

    velocity: float  # Change per hour
    acceleration: float  # Change in velocity per hour
    is_accelerating: bool  # True if growth is speeding up
    estimated_time_to_threshold: float | None  # Seconds until threshold (if predictable)
    confidence: float  # Confidence in predictions (0-1)


class VelocityTracker:
    """Tracks metric velocity and acceleration over time.

    This enables adaptive optimization:
    - Fast growth → Check more frequently
    - Slow growth → Check less frequently
    - Acceleration → Prepare for milestone
    - Deceleration → Relax check frequency
    """

    def __init__(self, max_history: int = 100):
        """Initialize velocity tracker.

        Args:
            max_history: Maximum number of snapshots to keep.
        """
        self.max_history = max_history
        self.snapshots: list[MetricSnapshot] = []

    def add_snapshot(self, value: int, timestamp: datetime | None = None) -> None:
        """Add a new metric snapshot.

        Args:
            value: Current metric value.
            timestamp: When this value was observed (defaults to now).
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        snapshot = MetricSnapshot(timestamp=timestamp, value=value)
        self.snapshots.append(snapshot)

        # Keep only recent history
        if len(self.snapshots) > self.max_history:
            self.snapshots = self.snapshots[-self.max_history :]

    def calculate_velocity(self, window_hours: float = 24.0) -> VelocityMetrics:
        """Calculate current velocity and acceleration.

        Args:
            window_hours: Time window for velocity calculation.

        Returns:
            Velocity metrics with predictions.
        """
        if len(self.snapshots) < 2:
            return VelocityMetrics(
                velocity=0.0,
                acceleration=0.0,
                is_accelerating=False,
                estimated_time_to_threshold=None,
                confidence=0.0,
            )

        # Calculate recent velocity (last window)
        recent_velocity = self._calculate_velocity_in_window(window_hours)

        # Calculate older velocity (previous window) for acceleration
        older_velocity = self._calculate_velocity_in_window(window_hours * 2, window_hours)

        # Acceleration is change in velocity
        acceleration = recent_velocity - older_velocity

        # Determine if accelerating
        is_accelerating = acceleration > 0.1  # Threshold for meaningful acceleration

        # Calculate confidence based on data availability
        confidence = min(len(self.snapshots) / 10.0, 1.0)  # Max confidence at 10+ snapshots

        return VelocityMetrics(
            velocity=recent_velocity,
            acceleration=acceleration,
            is_accelerating=is_accelerating,
            estimated_time_to_threshold=None,  # Will be calculated separately
            confidence=confidence,
        )

    def _calculate_velocity_in_window(
        self, window_hours: float, skip_hours: float = 0.0
    ) -> float:
        """Calculate velocity within a specific time window.

        Args:
            window_hours: Size of time window in hours.
            skip_hours: Hours to skip from now (for comparing periods).

        Returns:
            Velocity in changes per hour.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=window_hours + skip_hours)
        window_end = now - timedelta(hours=skip_hours)

        # Find snapshots in this window
        window_snapshots = [
            s for s in self.snapshots if window_start <= s.timestamp <= window_end
        ]

        if len(window_snapshots) < 2:
            return 0.0

        # Calculate velocity from first to last snapshot in window
        first = window_snapshots[0]
        last = window_snapshots[-1]

        time_diff_hours = (last.timestamp - first.timestamp).total_seconds() / 3600
        if time_diff_hours == 0:
            return 0.0

        value_diff = last.value - first.value
        return value_diff / time_diff_hours

    def estimate_time_to_threshold(
        self, current_value: int, threshold: int, velocity_metrics: VelocityMetrics
    ) -> float | None:
        """Estimate time until threshold is reached.

        Args:
            current_value: Current metric value.
            threshold: Target threshold.
            velocity_metrics: Current velocity metrics.

        Returns:
            Estimated seconds until threshold, or None if unpredictable.
        """
        if current_value >= threshold:
            return 0.0

        velocity = velocity_metrics.velocity

        # If velocity is too low, unpredictable
        if velocity < 0.1:
            return None

        # If velocity is negative, won't reach
        if velocity < 0:
            return None

        # If confidence is too low, don't predict
        if velocity_metrics.confidence < 0.3:
            return None

        remaining = threshold - current_value

        # Simple linear prediction
        hours_remaining = remaining / velocity

        # If accelerating, adjust estimate
        if velocity_metrics.is_accelerating and velocity_metrics.acceleration > 0:
            # Will reach faster than linear prediction
            hours_remaining *= 0.8  # Reduce by 20%

        return hours_remaining * 3600  # Convert to seconds

    def get_recommended_interval(
        self,
        velocity_metrics: VelocityMetrics,
        current_value: int,
        next_threshold: int | None,
        base_api_interval: int = 3600,
        base_screenshot_interval: int = 300,
    ) -> dict[str, Any]:
        """Get recommended check interval based on velocity.

        Args:
            velocity_metrics: Current velocity metrics.
            current_value: Current metric value.
            next_threshold: Next threshold to reach.
            base_api_interval: Base interval for API mode.
            base_screenshot_interval: Base interval for screenshot mode.

        Returns:
            Dictionary with recommended intervals and mode.
        """
        # Default to base intervals
        api_interval = base_api_interval
        screenshot_interval = base_screenshot_interval

        # Adjust based on velocity
        if velocity_metrics.velocity > 0:
            # Fast growth (> 10 per hour) → Check more frequently
            if velocity_metrics.velocity > 10:
                api_interval = int(base_api_interval * 0.5)  # 2x more frequent
                screenshot_interval = int(base_screenshot_interval * 0.7)

            # Very fast growth (> 50 per hour) → Check even more
            elif velocity_metrics.velocity > 50:
                api_interval = int(base_api_interval * 0.25)  # 4x more frequent
                screenshot_interval = int(base_screenshot_interval * 0.5)

            # Slow growth (< 1 per hour) → Check less frequently
            elif velocity_metrics.velocity < 1:
                api_interval = int(base_api_interval * 1.5)  # Slower
                screenshot_interval = int(base_screenshot_interval * 1.3)

        # If accelerating, increase frequency
        if velocity_metrics.is_accelerating:
            api_interval = int(api_interval * 0.8)
            screenshot_interval = int(screenshot_interval * 0.8)

        # Estimate time to threshold
        eta_seconds = None
        if next_threshold:
            eta_seconds = self.estimate_time_to_threshold(
                current_value, next_threshold, velocity_metrics
            )

            # If milestone is imminent (< 6 hours), switch to screenshot mode
            if eta_seconds and eta_seconds < 6 * 3600:
                recommended_mode = "screenshot"
            else:
                recommended_mode = "api"
        else:
            recommended_mode = "api"

        return {
            "api_interval": max(300, api_interval),  # Minimum 5 minutes
            "screenshot_interval": max(60, screenshot_interval),  # Minimum 1 minute
            "recommended_mode": recommended_mode,
            "eta_seconds": eta_seconds,
            "velocity": velocity_metrics.velocity,
            "acceleration": velocity_metrics.acceleration,
            "confidence": velocity_metrics.confidence,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for state persistence.

        Returns:
            Dictionary representation.
        """
        return {
            "snapshots": [
                {"timestamp": s.timestamp.isoformat(), "value": s.value}
                for s in self.snapshots
            ],
            "max_history": self.max_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VelocityTracker":
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation.

        Returns:
            VelocityTracker instance.
        """
        tracker = cls(max_history=data.get("max_history", 100))

        for snapshot_data in data.get("snapshots", []):
            timestamp = datetime.fromisoformat(snapshot_data["timestamp"])
            tracker.add_snapshot(snapshot_data["value"], timestamp)

        return tracker
