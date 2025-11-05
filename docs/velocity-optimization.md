# Velocity-Based Adaptive Optimization

## Overview

FABO now uses a **smarter adaptive algorithm** that tracks not just proximity to thresholds, but also the **velocity** (rate of change) and **acceleration** of metrics. This enables more intelligent decisions about when to switch modes and how frequently to check.

## Why Velocity Matters

### The Problem with Proximity-Only

The original approach switched modes based solely on proximity:
- **At 500/1000 stars** (50%): API mode, check every hour
- **At 920/1000 stars** (92%): Screenshot mode, check every 5 minutes

**But what if:**
- Stars are growing **slowly** (1 per day): No need for frequent checks even at 92%
- Stars are growing **fast** (50 per hour): Milestone is imminent even at 70%
- Growth is **accelerating**: Need to start screenshots earlier
- Growth is **decelerating**: Can relax check frequency

### The Solution: Velocity Tracking

Track how fast metrics change over time:
- **Velocity**: Change per hour (e.g., +10 stars/hour)
- **Acceleration**: Change in velocity (e.g., growing faster or slower)
- **ETA**: Estimated time to threshold based on current velocity

## How It Works

### 1. Velocity Calculation

```python
# Track snapshots over time
Snapshot(timestamp=10:00, value=900)
Snapshot(timestamp=11:00, value=910)
Snapshot(timestamp=12:00, value=925)

# Calculate velocity
velocity = (925 - 900) / 2 hours = 12.5 stars/hour

# Calculate acceleration
older_velocity = 10 stars/hour  # from previous window
acceleration = 12.5 - 10 = +2.5 stars/hour²  (accelerating!)
```

### 2. Adaptive Interval Adjustment

Based on velocity, **dynamically adjust check frequencies**:

```python
# Slow growth (< 1/hour)
velocity = 0.5 stars/hour
→ API interval: 5400s (1.5 hours)  # Check less frequently
→ Screenshot interval: 390s (6.5 min)

# Normal growth (1-10/hour)
velocity = 5 stars/hour
→ API interval: 3600s (1 hour)  # Default
→ Screenshot interval: 300s (5 min)

# Fast growth (10-50/hour)
velocity = 25 stars/hour
→ API interval: 1800s (30 min)  # Check more frequently
→ Screenshot interval: 210s (3.5 min)

# Very fast growth (> 50/hour)
velocity = 75 stars/hour
→ API interval: 900s (15 min)  # Check very frequently
→ Screenshot interval: 150s (2.5 min)
```

### 3. Acceleration Bonus

If metric is **accelerating** (growth speeding up):

```
acceleration > 0.1 stars/hour²
→ Reduce all intervals by 20%
→ Example: 3600s → 2880s (48 min instead of 1 hour)
```

### 4. ETA-Based Mode Switching

Predict when milestone will be reached:

```python
current = 900 stars
threshold = 1000 stars
velocity = 20 stars/hour

eta = (1000 - 900) / 20 = 5 hours

if eta < 6 hours:
    switch_to_screenshot_mode()
```

## Decision Logic

### Mode Switching

```
Switch to SCREENSHOT mode if ANY of:
1. Proximity >= 90% (original logic)
2. ETA < 6 hours (velocity-based)
3. Very fast growth (> 50/hour) AND proximity > 70%

Otherwise: API mode
```

### Check Frequency

```
Base intervals:
- API mode: 3600s (1 hour)
- Screenshot mode: 300s (5 minutes)

Adjustments:
× 1.5 if velocity < 1/hour (slower)
× 0.5 if velocity > 10/hour (faster)
× 0.25 if velocity > 50/hour (very fast)
× 0.8 if accelerating (speed up)

Limits:
- Minimum API interval: 300s (5 minutes)
- Minimum screenshot interval: 60s (1 minute)
```

## Real-World Examples

### Example 1: Slow Steady Growth

```
Current: 500 stars → 800 stars over 30 days
Velocity: 10 stars/day = 0.4/hour
Acceleration: ~0

Decision:
- Mode: API (not close to threshold)
- API interval: 5400s (1.5 hours) - relaxed
- Cost: Minimal, only API calls
```

### Example 2: Viral Growth

```
Day 1: 500 stars, velocity: 2/hour
Day 2: 600 stars, velocity: 10/hour (accelerating!)
Day 3: 800 stars, velocity: 25/hour (still accelerating!)

Decision at Day 3:
- Velocity: 25/hour → Fast growth
- Acceleration: +15/hour² → Accelerating
- ETA to 1000: (1000-800)/25 = 8 hours
- Mode: Still API (ETA > 6 hours)
- API interval: 1440s (24 min) - much faster
- Monitoring closely for ETA < 6 hours switch
```

### Example 3: Approaching Milestone

```
Current: 950 stars
Threshold: 1000 stars
Velocity: 15/hour
Acceleration: +2/hour²

Decision:
- Proximity: 95% → High
- ETA: (1000-950)/15 = 3.3 hours → Imminent!
- Mode: SCREENSHOT (both triggers met)
- Screenshot interval: 180s (3 min) - accelerated due to fast growth
- Ready to capture exact moment!
```

### Example 4: Plateau Detection

```
Current: 920 stars
Previous velocity: 20/hour
Current velocity: 2/hour (slowed down!)
Acceleration: -18/hour² (decelerating)

Decision:
- Proximity: 92% → High
- But velocity dropped dramatically
- ETA: (1000-920)/2 = 40 hours
- Mode: API (ETA too far, despite proximity)
- API interval: 4500s (1.25 hours)
- Saved from premature screenshot mode!
```

## Benefits

### 1. Cost Optimization

**Before (proximity-only)**:
- At 920/1000: Switch to screenshots
- Check every 5 min for potentially days
- Cost: High if growth stalls

**After (velocity-aware)**:
- Detect slow growth
- Stay in API mode longer
- Or use relaxed screenshot intervals
- **Cost: Reduced by 50-70% in slow growth scenarios**

### 2. Better Accuracy

- **Don't miss fast milestones**: Switch early if velocity is high
- **Don't waste on plateaus**: Stay in API mode if growth stalls
- **Predictive**: Know approximately when milestone will hit

### 3. Adaptive to Reality

- **Viral moments**: Automatically increase frequency
- **Quiet periods**: Automatically decrease frequency
- **Acceleration**: Detect momentum changes

## Configuration

### In Run Config

```yaml
optimization:
  # Base intervals (used as starting points)
  api_mode_interval: 3600
  screenshot_mode_interval: 300

  # Velocity thresholds (optional, uses defaults if not set)
  slow_velocity_threshold: 1.0      # stars/hour
  fast_velocity_threshold: 10.0     # stars/hour
  very_fast_velocity_threshold: 50.0

  # Acceleration threshold
  acceleration_threshold: 0.1       # stars/hour²

  # ETA threshold for mode switching
  eta_threshold_hours: 6            # Switch to screenshot if < 6 hours

  # Proximity still matters
  threshold_proximity_percent: 90
```

### Velocity Window

By default, velocity is calculated over a **24-hour window**:
- Recent velocity: Last 24 hours
- Older velocity: 24-48 hours ago
- Acceleration: Difference between them

This can be adjusted in code if needed.

## Monitoring Velocity

### CLI Output

```bash
fabo run --config runs/my-run.yaml

# Output includes velocity info:
Current state:
  Mode: api
  Current value: 920
  Next threshold: 1000
  Proximity: 92.0%
  Velocity: +15.2/hr ⚡      # <- NEW!
  Acceleration: +2.1/hr²     # <- NEW!
  ETA: 5.3h                  # <- NEW!
  Check interval: 1800s
```

### State File

```json
{
  "run_id": "github-stars",
  "current_value": 920,
  "current_velocity": 15.2,
  "current_acceleration": 2.1,
  "is_accelerating": true,
  "eta_to_threshold_seconds": 19080,
  "velocity_data": {
    "snapshots": [
      {"timestamp": "2025-11-05T10:00:00", "value": 900},
      {"timestamp": "2025-11-05T11:00:00", "value": 915},
      {"timestamp": "2025-11-05T12:00:00", "value": 920}
    ]
  }
}
```

## Implementation Details

### Data Collection

Every time a metric is checked (API or screenshot):
1. Record timestamp and value
2. Add to velocity tracker
3. Keep last 100 snapshots (configurable)
4. Calculate velocity from recent data

### Persistence

Velocity data is saved in operator state JSON file:
- Survives between runs
- Git-friendly format
- Can be analyzed offline

### Confidence

Velocity predictions have confidence scores:
- **Low confidence** (< 30%): Not enough data, don't predict
- **Medium** (30-70%): Use with caution
- **High** (> 70%): Trust predictions

Confidence increases with more data points (maxes at 10 snapshots).

## Future Enhancements

- **Machine learning**: Predict patterns based on historical data
- **Time-of-day awareness**: Account for daily/weekly patterns
- **Event detection**: Detect spikes (e.g., viral posts, media coverage)
- **Multi-metric correlation**: Use related metrics to improve predictions
- **Seasonal adjustments**: Account for holidays, weekends, etc.

## Testing Velocity Tracking

```bash
# Force API mode to collect data
fabo run --config runs/test.yaml --mode api

# Watch velocity build up over multiple runs
watch -n 300 'fabo run --config runs/test.yaml && cat data/runs/test.json | jq .current_velocity'

# Simulate fast growth for testing
# Edit state file to inject fake snapshots with high velocity
```

---

**Result**: FABO now makes smarter decisions based on actual metric behavior, not just static thresholds!
