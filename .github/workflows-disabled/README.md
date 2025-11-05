# GitHub Actions - Disabled During Development

The GitHub Actions workflow has been moved to `.github/workflows-disabled/` to prevent automatic runs during development.

## Why Disabled?

During development, we're implementing a **smarter adaptive algorithm** that:
- Tracks metric velocity (rate of change)
- Detects acceleration (is growth speeding up or slowing down?)
- Dynamically adjusts check frequency based on these factors
- Predicts when milestones will be reached

## Re-enabling

Once the adaptive algorithm is stable, move the workflow back:

```bash
mv .github/workflows-disabled/fabo-check.yml.disabled .github/workflows/fabo-check.yml
```

Or manually trigger runs:

```bash
# Local testing
fabo run --config runs/my-run.yaml

# Cron job (when ready)
*/30 * * * * cd /path/to/fabo && fabo run --config runs/my-run.yaml
```
