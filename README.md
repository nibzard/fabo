<h1 align="center">
 <a href="https://github.com/nkkko/fabo">
   <img src="logo.png" alt="Logo" width="250" height="250">
 </a>
</h1>

<div align="center">
 <strong>FABO - Fabulous screen-shooter of your social media milestones</strong>
 <br />
 An intelligent milestone tracker that automatically captures screenshots when your metrics reach important thresholds.
 <br />
 <br />
 <a href="https://github.com/nkkko/fabo/issues/new?assignees=&labels=bug&template=01_BUG_REPORT.md&title=bug%3A+">Report a Bug</a>
 ·
 <a href="https://github.com/nkkko/fabo/issues/new?assignees=&labels=enhancement&template=02_FEATURE_REQUEST.md&title=feat%3A+">Request a Feature</a>
 .
 <a href="https://github.com/nkkko/fabo/discussions">Ask a Question</a>
</div>

<div align="center">
<br />

[![license](https://img.shields.io/github/license/nkkko/fabo.svg?style=flat-square)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![made with hearth](https://img.shields.io/badge/made%20with%20%E2%99%A5%20by-nkkko-ff1414.svg?style=flat-square)](https://github.com/nkkko)

</div>

---

## 🎯 What Makes FABO Different?

**Smart Optimization**: FABO doesn't just poll APIs constantly. It intelligently switches between API mode (cheap, fast) and screenshot mode (accurate, visual) based on proximity to your milestones.

**LLM-Powered Validation**: Uses Claude 3.5 Sonnet or GPT-4 Vision to extract metrics directly from screenshots - perfect for platforms with restricted APIs or when you need visual proof.

**CI/CD Native**: Designed for GitHub Actions. Each operator run is independent and can be triggered via cron, workflows, or manually.

**Modular Architecture**: Domain-Driven Design with clean separation. Add new platforms by implementing a simple operator interface.

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/nkkko/fabo.git && cd fabo
uv sync

# Configure
cp .env.example .env
# Edit .env with your API keys

# Create a run config
cat > runs/my-stars.yaml <<EOF
id: github-myrepo-stars
platform: github
target:
  owner: myusername
  repo: myrepo
metrics:
  - type: stars
    thresholds: [100, 500, 1000]
optimization:
  api_mode_interval: 3600
  screenshot_mode_interval: 300
  threshold_proximity_percent: 90
enabled: true
EOF

# Run it!
fabo run --config runs/my-stars.yaml
```

See [Quick Start Guide](docs/quick-start.md) for detailed instructions.

## 📖 How It Works

### The Smart Optimization Strategy

FABO uses intelligent mode switching to minimize costs while capturing exact milestone moments:

- **Far from threshold (< 90%)**: Use API mode → Check hourly → $0 cost
- **Near threshold (≥ 90%)**: Switch to screenshot mode → Check every 5min → LLM validates
- **Milestone reached**: Save screenshot → Record milestone → Back to API mode

**Cost Example**: Tracking to 1,000 stars costs ~$40-50 vs. $2,000+ with constant screenshots!

## ✨ Features

### Core Capabilities
- ✅ **Multi-Platform Support**: GitHub, Twitter/X, LinkedIn (extensible)
- ✅ **Dual-Mode Operation**: Smart switching between API and screenshot modes
- ✅ **LLM Vision**: Claude 3.5 Sonnet / GPT-4V for metric extraction
- ✅ **GitHub Actions Ready**: Built for CI/CD workflows
- ✅ **Cron Compatible**: Independent execution model
- ✅ **State Management**: Continuous tracking across runs
- ✅ **Cost Optimization**: Minimize API calls and screenshots

### Platform Support

| Platform | API Mode | Screenshot Mode | Status |
|----------|----------|-----------------|--------|
| GitHub | ✅ Stars, Forks, Watchers | ✅ | Production |
| Twitter/X | ✅ Followers, Tweets | ✅ | Production |
| LinkedIn | ⚠️ Limited | ✅ | Beta |
| YouTube | 📋 Planned | 📋 Planned | Roadmap |
| Instagram | 📋 Planned | 📋 Planned | Roadmap |

## 🏗️ Architecture

FABO uses **Domain-Driven Design** with smart operators that make intelligent decisions. See [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) for detailed documentation.

## 🤖 GitHub Actions

Create `.github/workflows/fabo-check.yml`:

```yaml
name: FABO Milestone Check
on:
  schedule:
    - cron: '*/30 * * * *'
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv sync
      - env:
          STEEL_API_KEY: ${{ secrets.STEEL_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: uv run fabo run --config runs/my-run.yaml
```

## 📚 Documentation

- [Quick Start Guide](docs/quick-start.md) - Get up and running in 5 minutes
- [Architecture V2](ARCHITECTURE_V2.md) - Smart optimization design  
- [Operator Guide](docs/operators.md) - Add new platforms

## 🗺️ Roadmap

- [x] Smart dual-mode operators
- [x] LLM vision extraction
- [x] GitHub Actions support
- [ ] Database persistence
- [ ] REST API & Web UI
- [ ] YouTube & Instagram

## 📄 License

MIT License - see [LICENSE](LICENSE).

## 🙏 Acknowledgements

- Powered by [Steel.dev](https://steel.dev) & [Anthropic Claude](https://anthropic.com)
- Inspired by the real FABO who never missed a milestone

---

<div align="center">
<strong>Never miss a milestone again! 🎉</strong>
<br />
Made with ❤️ by <a href="https://github.com/nkkko">nkkko</a>
</div>
