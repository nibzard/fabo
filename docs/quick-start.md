# FABO Quick Start Guide

## Overview

FABO is an intelligent milestone tracker that automatically captures screenshots when your social media metrics reach important thresholds. It uses smart optimization to minimize costs while maximizing accuracy.

## Key Features

- **Smart Mode Switching**: Uses API when far from threshold, switches to screenshots when close
- **LLM Validation**: Extracts metrics from screenshots using Claude/GPT-4V
- **Cost Optimized**: Only screenshots when necessary
- **GitHub Actions Ready**: Perfect for automated CI/CD workflows
- **Modular Operators**: Easy to add new platforms

## Installation

```bash
# Clone repository
git clone https://github.com/nkkko/fabo.git
cd fabo

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

## Required API Keys

### Minimum Setup (API Mode Only)
```bash
GITHUB_TOKEN=ghp_your_token_here
```

### Full Setup (Screenshot Mode)
```bash
# Steel.dev for screenshots (required for screenshot mode)
STEEL_API_KEY=your_steel_api_key

# Platform APIs
GITHUB_TOKEN=ghp_your_token_here
TWITTER_BEARER_TOKEN=your_twitter_token

# LLM for screenshot analysis (at least one)
ANTHROPIC_API_KEY=sk-ant-your_key
# OR
OPENAI_API_KEY=sk-your_key
```

## Creating Your First Run

### 1. Create Run Configuration

Create `runs/my-first-run.yaml`:

```yaml
id: github-myusername-myrepo-stars
name: "My Repository Stars"
description: "Track stars for my awesome project"

platform: github
target:
  owner: myusername
  repo: myrepo

metrics:
  - type: stars
    thresholds: [10, 50, 100, 500, 1000]

optimization:
  api_mode_interval: 3600          # Check hourly when far
  screenshot_mode_interval: 300     # Check every 5min when close
  threshold_proximity_percent: 90   # Switch at 90%

enabled: true
```

### 2. Test Your Configuration

```bash
# Dry run to see what would happen
fabo run --config runs/my-first-run.yaml --dry-run

# Run in API mode
fabo run --config runs/my-first-run.yaml --mode api

# Force screenshot mode (for testing)
fabo run --config runs/my-first-run.yaml --force-screenshot
```

### 3. Check the Results

```bash
# View state
cat data/runs/github-myusername-myrepo-stars.json

# View milestones (if any were captured)
ls -la data/milestones/

# View screenshots
ls -la screenshots/
```

## How It Works

### The Smart Optimization Flow

```
1. START
   ├─ Load state (or create new)
   ├─ Calculate proximity to threshold
   └─ Determine mode (API or Screenshot)

2. FAR FROM THRESHOLD (< 90%)
   ├─ Use API mode
   ├─ Make cheap API call
   ├─ Update state
   └─ Schedule next check in 1 hour

3. NEAR THRESHOLD (>= 90%)
   ├─ Switch to Screenshot mode
   ├─ Capture screenshot with Steel.dev
   ├─ Extract metric with LLM vision
   ├─ Validate confidence score
   └─ Schedule next check in 5 minutes

4. MILESTONE REACHED
   ├─ Save final screenshot
   ├─ Create milestone record
   ├─ Advance to next threshold
   └─ Return to API mode
```

### Example Scenario

**Goal**: Capture screenshot at 1,000 stars

**Timeline**:
- **Day 1** (500 stars): API check every hour = 24 API calls, $0
- **Day 7** (800 stars): API check every hour = 24 API calls, $0
- **Day 14** (950 stars): Switch to screenshots every 5min = 288 screenshots/day
- **Day 16** (1,000 stars): Milestone captured! 🎉

**Total Cost**: ~$30-40 for screenshot period vs. $0 for API period

## GitHub Actions Setup

### 1. Add Secrets to Repository

Go to Settings → Secrets and variables → Actions:

```
STEEL_API_KEY
GITHUB_TOKEN (automatically available)
ANTHROPIC_API_KEY
TWITTER_BEARER_TOKEN (if needed)
```

### 2. Create Workflow

Copy `.github/workflows/fabo-check.yml` to your repository.

### 3. Enable Actions

- Go to Actions tab
- Enable workflows
- Watch it run every 30 minutes!

### 4. Manual Trigger

```bash
# Via GitHub UI: Actions → FABO Milestone Check → Run workflow

# Via gh CLI:
gh workflow run fabo-check.yml
```

## Cron Setup (Local/Server)

```bash
# Edit crontab
crontab -e

# Add FABO checks
# Check every 30 minutes
*/30 * * * * cd /path/to/fabo && uv run fabo run --config runs/my-run.yaml >> /var/log/fabo.log 2>&1

# Check multiple configs
0 * * * * cd /path/to/fabo && uv run fabo run --config runs/github-stars.yaml
30 * * * * cd /path/to/fabo && uv run fabo run --config runs/twitter-followers.yaml
```

## Monitoring Your Runs

### Check Status

```bash
# View current state
fabo status

# View recent milestones
fabo list

# View specific run state
cat data/runs/my-run-id.json | jq
```

### State File Example

```json
{
  "id": "...",
  "run_id": "github-myrepo-stars",
  "platform": "github",
  "current_value": 950,
  "next_threshold": 1000,
  "mode": "screenshot",
  "total_checks": 145,
  "api_calls_made": 120,
  "screenshots_taken": 25,
  "check_interval": 300
}
```

### Cost Tracking

```bash
# Run generates cost estimate
fabo run --config runs/my-run.yaml

# Output includes:
# Estimated Costs:
#   API calls: $0.00
#   Screenshots: $1.25
#   LLM vision: $0.25
#   Total: $1.50
```

## Common Use Cases

### 1. Track Competitor (No API Access)

```yaml
id: competitor-stars
platform: github
target:
  owner: competitor
  repo: their-repo

metrics:
  - type: stars
    thresholds: [10000, 50000, 100000]

optimization:
  mode: screenshot_only  # No API, always screenshot
  screenshot_mode_interval: 3600  # Every hour
```

### 2. Multiple Metrics on Same Platform

```yaml
id: github-myrepo-all
platform: github
target:
  owner: myusername
  repo: myrepo

metrics:
  - type: stars
    thresholds: [100, 500, 1000]
  - type: forks
    thresholds: [10, 50, 100]
  - type: watchers
    thresholds: [50, 100, 500]
```

### 3. High-Value Milestone (Extra Careful)

```yaml
id: important-milestone
platform: twitter
target:
  username: myhandle

metrics:
  - type: followers
    thresholds: [10000]  # Just one important threshold

optimization:
  threshold_proximity_percent: 95  # Start screenshots at 95%
  screenshot_mode_interval: 60     # Check every minute!
  min_confidence: 0.95             # Very high confidence required
  max_retries: 5                   # Retry more times
```

## Troubleshooting

### "No LLM API key found"

Make sure at least one of these is set:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# OR
export OPENAI_API_KEY=sk-...
```

### "Rate limit exceeded"

Switch to screenshot mode:
```bash
fabo run --config runs/my-run.yaml --mode screenshot
```

### "Low confidence extraction"

Check the screenshot manually:
```bash
ls -la temp_screenshots/
open temp_screenshots/my-run-id_check.png
```

Adjust confidence threshold in config:
```yaml
optimization:
  min_confidence: 0.75  # Lower if needed
```

### GitHub Actions: "Permission denied"

Make sure workflow has write permissions:
```yaml
permissions:
  contents: write
```

## Next Steps

- [Full Architecture Documentation](../ARCHITECTURE_V2.md)
- [Operator Development Guide](operators.md)
- [GitHub Actions Examples](.github/workflows/)
- [Advanced Configuration](configuration.md)

## Need Help?

- [Open an Issue](https://github.com/nkkko/fabo/issues)
- [Discussions](https://github.com/nkkko/fabo/discussions)
- [Documentation](https://github.com/nkkko/fabo/tree/main/docs)
