# FABO Architecture - Smart Screenshot Optimization

## Core Philosophy

FABO is designed to **minimize API calls and screenshot operations** while **maximizing accuracy** in capturing milestone moments. The system intelligently switches from API polling to screenshot-based monitoring as metrics approach thresholds.

## Key Concepts

### 1. Operator Modes

Each operator has two operational modes:

#### **API Mode (Far from Threshold)**
- Uses platform APIs to check current metrics
- Minimal cost and rate limit impact
- Runs less frequently
- Example: Checking GitHub stars when at 500, target is 1000

#### **Screenshot Mode (Near Threshold)**
- Takes periodic screenshots of the metric page
- Uses multimodal LLM to extract metric from image
- Captures exact visual moment
- Example: When at 980 stars approaching 1000, screenshot every 5 minutes

### 2. Smart Optimization Algorithm

```
Current Value: 950
Threshold: 1000
Progress: 95%

Decision Logic:
IF progress < 80%:
    USE API Mode (check every 1 hour)
ELIF progress < 95%:
    USE API Mode (check every 15 minutes)
ELSE:
    USE Screenshot Mode (check every 5 minutes)
    USE LLM validation
```

### 3. Multimodal LLM Validation

Screenshots are validated using vision models (Claude 3.5 Sonnet, GPT-4V) to:
- Extract metric value from screenshot
- Confirm the correct page/metric is shown
- Validate timestamp/freshness
- Return structured data

### 4. Standalone Execution

Each operator run is independent and can be triggered by:
- **Cron**: Traditional scheduled tasks
- **GitHub Actions**: CI/CD workflows
- **Manual**: CLI commands
- **API**: REST endpoint triggers

## Updated Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Trigger Sources                          │
│     (Cron, GitHub Actions, CLI, API)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 Operator Runner                             │
│  • Loads configuration                                      │
│  • Initializes operator                                     │
│  • Executes check cycle                                     │
│  • Persists state                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Platform Operator                            │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │  1. Determine Mode (API vs Screenshot)            │    │
│  │     • Calculate proximity to threshold            │    │
│  │     • Check last update time                      │    │
│  │     • Consider rate limits                        │    │
│  └───────────────────────────────────────────────────┘    │
│                       │                                     │
│         ┌─────────────┴─────────────┐                      │
│         ▼                           ▼                       │
│  ┌─────────────┐            ┌─────────────────┐           │
│  │  API Mode   │            │ Screenshot Mode │           │
│  │             │            │                 │           │
│  │ • API call  │            │ • Steel.dev    │           │
│  │ • Parse     │            │ • Capture      │           │
│  │ • Compare   │            │ • LLM extract  │           │
│  └─────────────┘            └─────────────────┘           │
│         │                           │                       │
│         └─────────────┬─────────────┘                      │
│                       ▼                                     │
│  ┌───────────────────────────────────────────────────┐    │
│  │  3. Threshold Detection                           │    │
│  │     • Compare current vs threshold                │    │
│  │     • Validate with confidence score              │    │
│  └───────────────────────────────────────────────────┘    │
│                       │                                     │
│                       ▼                                     │
│  ┌───────────────────────────────────────────────────┐    │
│  │  4. Milestone Capture                             │    │
│  │     • Save final screenshot                       │    │
│  │     • Create milestone record                     │    │
│  │     • Update state for next run                   │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Operator State Management

Each operator maintains state between runs:

```python
{
  "run_id": "github-nkkko-fabo-stars",
  "platform": "github",
  "target": {"owner": "nkkko", "repo": "fabo"},
  "metric": "stars",
  "last_check": "2025-11-05T10:30:00Z",
  "current_value": 950,
  "thresholds": [1000, 5000, 10000],
  "next_threshold": 1000,
  "mode": "screenshot",  # or "api"
  "check_interval": 300,  # 5 minutes in screenshot mode
  "milestone_reached": false,
  "screenshots_taken": 5,
  "api_calls_made": 120
}
```

## LLM-Based Metric Extraction

### Prompt Template

```
You are analyzing a screenshot of a GitHub repository page.

Extract the following metrics from the image:
1. Repository name
2. Number of stars
3. Number of forks
4. Number of watchers

Return your response in JSON format:
{
  "repository": "owner/repo",
  "stars": 1234,
  "forks": 56,
  "watchers": 78,
  "timestamp_visible": true,
  "confidence": 0.95
}

If you cannot clearly read a metric, return null for that field.
```

### Validation

- **Confidence threshold**: Only accept extractions with confidence > 0.85
- **Sanity checks**: Validate metric isn't decreasing (except for temporary API glitches)
- **Multi-attempt**: Take multiple screenshots if confidence is low

## Configuration Structure

### Multiple Run Configurations

```yaml
runs:
  # Run 1: Track main repository stars
  - id: fabo-stars-main
    platform: github
    target:
      owner: nkkko
      repo: fabo
    metrics:
      - type: stars
        thresholds: [100, 500, 1000, 5000]
    optimization:
      api_mode_interval: 3600  # 1 hour when far
      screenshot_mode_interval: 300  # 5 minutes when near
      threshold_proximity_percent: 90  # Switch at 90%

  # Run 2: Track Twitter followers
  - id: twitter-followers
    platform: twitter
    target:
      username: nkkko
    metrics:
      - type: followers
        thresholds: [1000, 5000, 10000]
    optimization:
      api_mode_interval: 7200
      screenshot_mode_interval: 600
      threshold_proximity_percent: 95

  # Run 3: Track competitor (screenshot only, no API)
  - id: competitor-watch
    platform: github
    target:
      owner: competitor
      repo: project
    metrics:
      - type: stars
        thresholds: [10000, 50000]
    optimization:
      mode: screenshot_only  # No API access
      screenshot_interval: 3600
```

## GitHub Actions Integration

```yaml
# .github/workflows/fabo-check.yml
name: FABO Milestone Check

on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  check-milestones:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run FABO operator
        env:
          STEEL_API_KEY: ${{ secrets.STEEL_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          fabo run --config runs/fabo-stars-main.yaml

      - name: Upload screenshots
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: screenshots
          path: screenshots/

      - name: Commit milestone data
        if: success()
        run: |
          git config user.name "FABO Bot"
          git config user.email "fabo@nkkko.com"
          git add data/milestones.json
          git diff --quiet && git diff --staged --quiet || \
            git commit -m "Update milestone data [skip ci]"
          git push
```

## Cost Optimization Examples

### Scenario 1: Far from Threshold
- **Current**: 500 stars
- **Threshold**: 1000 stars
- **Strategy**: API check every 1 hour
- **Daily Cost**: 24 API calls × $0 = $0

### Scenario 2: Approaching Threshold
- **Current**: 950 stars
- **Threshold**: 1000 stars
- **Strategy**: Screenshot every 5 minutes
- **Daily Cost**: 288 screenshots × $0.05 = $14.40
- **Duration**: ~2-3 days typically = $30-45 total

### Scenario 3: No API Access
- **Current**: Unknown
- **Threshold**: 10,000 stars
- **Strategy**: Screenshot every hour, LLM extraction
- **Daily Cost**: 24 screenshots + 24 LLM calls = ~$5/day

## Benefits of This Approach

1. **Cost Efficient**: Only screenshot when necessary
2. **Rate Limit Friendly**: Minimize API calls
3. **Accurate Capture**: Screenshots show exact visual moment
4. **API-Independent**: Can track competitors without API access
5. **Verifiable**: Visual proof of milestone
6. **Flexible**: Works with any platform (web scraping fallback)
7. **Modular**: Each run is independent
8. **CI/CD Native**: Perfect for GitHub Actions

## State Persistence

Operators save state locally or to Git:

```
data/
├── runs/
│   ├── fabo-stars-main.json
│   ├── twitter-followers.json
│   └── competitor-watch.json
├── milestones/
│   ├── 2025-11-05-github-stars-1000.json
│   └── 2025-11-04-twitter-followers-5000.json
└── screenshots/
    ├── 2025-11-05-10-30-github-nkkko-fabo.png
    └── 2025-11-05-10-35-github-nkkko-fabo.png
```

## Operator Runner CLI

```bash
# Run specific configuration
fabo run --config runs/fabo-stars-main.yaml

# Run with explicit mode
fabo run --config runs/fabo-stars-main.yaml --mode screenshot

# Dry run (show what would happen)
fabo run --config runs/fabo-stars-main.yaml --dry-run

# Force screenshot regardless of proximity
fabo run --config runs/fabo-stars-main.yaml --force-screenshot

# Run all configurations
fabo run --all
```

## Next Implementation Steps

1. Refactor operators to support dual-mode operation
2. Add LLM vision service (Claude/GPT-4V integration)
3. Implement smart threshold proximity detection
4. Create standalone runner for cron/GH Actions
5. Build state management system
6. Add screenshot comparison and validation
7. Create GitHub Actions workflow templates
