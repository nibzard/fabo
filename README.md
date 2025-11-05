<h1 align="center">
 <a href="https://github.com/nkkko/fabo">
   <img src="logo.png" alt="Logo" width="250" height="250">
 </a>
</h1>

<div align="center">
 <strong>FABO - Fabulous screen-shooter of your social media milestones</strong>
 <br />
 A command-line tool that celebrates your social media achievements by automagically capturing screenshots of major milestones.
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

<details open="open">
<summary>Table of Contents</summary>

- [About](#about)
- [Features](#features)
- [Architecture](#architecture)
- [Built With](#built-with)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Commands](#cli-commands)
  - [API](#api)
- [Development](#development)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

</details>

---

## About

FABO is a Python-based CLI tool that tracks social media milestones across multiple platforms and automatically captures screenshots when milestones are reached. Never miss celebrating your achievements again!

### The Story

FABO was born from a real need while tracking [Daytona](https://github.com/daytonaio/daytona) as it approached 4,000 stars. Despite our best intentions, we consistently failed to capture the exact moment milestones were reached. Our teammate Fabo always managed to save the day, so we built this tool in their honor!

## Features

- **Multi-Platform Support**: Track GitHub, Twitter/X, and LinkedIn (extensible to more platforms)
- **Automated Screenshot Capture**: Uses [Steel.dev](https://steel.dev) headless browser API for high-quality screenshots
- **Configurable Thresholds**: Set custom milestone values for each platform and metric
- **Scheduled Checks**: Automatic periodic checking with configurable intervals
- **Domain-Driven Design**: Clean, modular architecture for easy extension
- **REST API**: Programmatic access for integrations
- **CLI Interface**: User-friendly command-line interface
- **Type-Safe**: Full type hints with mypy strict mode
- **Well-Documented**: Extensive inline documentation and guides

### Supported Platforms

| Platform | Metrics | Status |
|----------|---------|--------|
| GitHub | Stars, Forks, Watchers, Issues | ✅ Implemented |
| Twitter/X | Followers, Tweets | ✅ Implemented |
| LinkedIn | Connections, Followers | ⚠️ Limited (API restrictions) |
| YouTube | Subscribers, Views | 📋 Planned |
| Instagram | Followers, Posts | 📋 Planned |

## Architecture

FABO follows **Domain-Driven Design (DDD)** principles with a clean, layered architecture:

```
┌─────────────────────────────────────────┐
│         Interface Layer                 │
│    (CLI, REST API, Web UI future)       │
├─────────────────────────────────────────┤
│       Application Layer                 │
│  (Use Cases, DTOs, Orchestration)       │
├─────────────────────────────────────────┤
│         Domain Layer                    │
│ (Entities, Value Objects, Repositories) │
├─────────────────────────────────────────┤
│      Infrastructure Layer               │
│ (Operators, Steel.dev, Database, Cron)  │
└─────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

## Built With

- **Python 3.12+** - Modern Python with latest features
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager
- **[Steel.dev](https://steel.dev)** - Headless browser API for screenshots
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern web framework for API
- **[Typer](https://typer.tiangolo.com/)** - CLI framework
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Database ORM
- **[APScheduler](https://apscheduler.readthedocs.io/)** - Task scheduling

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- [Steel.dev](https://steel.dev) API key (free tier available)
- Platform API credentials (GitHub token, Twitter bearer token, etc.)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/nkkko/fabo.git
cd fabo
```

2. **Install dependencies using uv**

```bash
uv sync
```

3. **Copy environment template**

```bash
cp .env.example .env
```

4. **Edit `.env` with your credentials**

```bash
# Required
STEEL_API_KEY=your-steel-api-key

# Platform credentials (as needed)
GITHUB_TOKEN=your-github-token
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
```

5. **Copy configuration template**

```bash
cp config.yaml.example config.yaml
```

6. **Edit `config.yaml` to configure platforms and thresholds**

### Configuration

See [docs/configuration.md](docs/configuration.md) for detailed configuration options.

## Usage

### CLI Commands

```bash
# Check for milestones now
fabo check

# Check specific platform
fabo check --platform github

# Configure a platform
fabo configure github

# List captured milestones
fabo list

# Show status
fabo status

# Start API server
fabo serve

# Enable scheduler for automatic checks
fabo schedule --enable --interval 3600
```

### API

Start the API server:

```bash
fabo serve
```

Access API documentation at `http://localhost:8000/docs`

Example endpoints:
- `POST /api/v1/milestones/check` - Trigger milestone check
- `GET /api/v1/milestones` - List milestones
- `GET /api/v1/platforms` - List configured platforms

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
pytest

# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

### Project Structure

```
fabo/
├── src/fabo/
│   ├── domain/              # Domain models
│   ├── application/         # Use cases
│   ├── infrastructure/      # External services
│   └── interfaces/          # CLI, API
├── tests/                   # Test suite
├── docs/                    # Documentation
└── pyproject.toml          # Project config
```

## Roadmap

- [x] Core DDD architecture
- [x] GitHub operator
- [x] Twitter operator
- [x] Steel.dev integration
- [x] CLI interface
- [ ] Database persistence (SQLite/PostgreSQL)
- [ ] Scheduler implementation
- [ ] REST API implementation
- [ ] Web UI
- [ ] Multi-user support
- [ ] Cloud storage for screenshots
- [ ] Notification channels (email, Slack, Discord)
- [ ] AI-powered milestone predictions

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Inspired by the real-life FABO who never missed a milestone
- Built while tracking [Daytona](https://github.com/daytonaio/daytona) on its journey to GitHub stardom
- Powered by [Steel.dev](https://steel.dev) for reliable screenshot capture
- Special thanks to all contributors and the open-source community

---

<div align="center">
Made with ❤️ by <a href="https://github.com/nkkko">nkkko</a>
</div>
