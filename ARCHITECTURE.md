# FABO Architecture Documentation

## Overview

FABO (Fabulous screen-shooter of your social media milestones) is a Python-based CLI tool that tracks social media milestones and automatically captures screenshots using Steel.dev's headless browser API.

## Architecture Pattern: Domain-Driven Design (DDD)

### Core Principles

1. **Domain Layer**: Business logic and rules
2. **Application Layer**: Use cases and orchestration
3. **Infrastructure Layer**: External services and persistence
4. **Interface Layer**: APIs, CLI, and future web interface

## Project Structure

```
fabo/
├── src/
│   └── fabo/
│       ├── domain/               # Domain Layer (Business Logic)
│       │   ├── entities/         # Core business entities
│       │   │   ├── milestone.py
│       │   │   ├── platform.py
│       │   │   └── screenshot.py
│       │   ├── value_objects/    # Immutable value objects
│       │   │   ├── milestone_type.py
│       │   │   └── platform_credentials.py
│       │   ├── repositories/     # Repository interfaces
│       │   │   ├── milestone_repository.py
│       │   │   └── screenshot_repository.py
│       │   └── services/         # Domain services
│       │       └── milestone_detector.py
│       │
│       ├── application/          # Application Layer (Use Cases)
│       │   ├── use_cases/
│       │   │   ├── check_milestones.py
│       │   │   ├── capture_screenshot.py
│       │   │   └── schedule_checks.py
│       │   └── dtos/            # Data Transfer Objects
│       │       ├── milestone_dto.py
│       │       └── screenshot_dto.py
│       │
│       ├── infrastructure/       # Infrastructure Layer
│       │   ├── operators/       # Platform-specific implementations
│       │   │   ├── base_operator.py
│       │   │   ├── github_operator.py
│       │   │   ├── twitter_operator.py
│       │   │   └── linkedin_operator.py
│       │   ├── screenshot/      # Screenshot service
│       │   │   ├── steel_client.py
│       │   │   └── screenshot_service.py
│       │   ├── persistence/     # Data storage
│       │   │   ├── json_repository.py
│       │   │   └── sqlite_repository.py
│       │   ├── scheduling/      # Cron/scheduler
│       │   │   └── scheduler.py
│       │   └── config/          # Configuration
│       │       └── settings.py
│       │
│       └── interfaces/          # Interface Layer
│           ├── api/             # REST API (FastAPI)
│           │   ├── main.py
│           │   ├── routes/
│           │   │   ├── milestones.py
│           │   │   └── platforms.py
│           │   └── middleware/
│           │       └── auth.py
│           └── cli/             # CLI Interface
│               ├── main.py
│               └── commands/
│                   ├── check.py
│                   ├── configure.py
│                   └── schedule.py
│
├── tests/                       # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                        # Documentation
│   ├── api/
│   ├── operators/
│   └── guides/
│
├── pyproject.toml              # Project configuration (uv)
├── README.md
├── ARCHITECTURE.md
└── .env.example

```

## Domain Model

### Entities

#### Milestone
- Represents a social media milestone event
- Properties: platform, milestone_type, value, timestamp, screenshot_id
- Behaviors: is_new(), should_notify()

#### Platform
- Represents a social media platform configuration
- Properties: name, credentials, check_frequency, milestone_thresholds
- Behaviors: validate_credentials(), get_current_stats()

#### Screenshot
- Represents a captured screenshot
- Properties: url, file_path, timestamp, milestone_id, metadata
- Behaviors: save(), get_size()

### Value Objects

#### MilestoneType
- Enum: GITHUB_STARS, GITHUB_FORKS, TWITTER_FOLLOWERS, LINKEDIN_CONNECTIONS
- Immutable representation of milestone types

#### PlatformCredentials
- Secure credential storage
- Encrypted at rest

## Application Services

### Use Cases

1. **CheckMilestonesUseCase**
   - Checks all configured platforms for new milestones
   - Triggers screenshot capture when milestones are reached
   - Sends notifications

2. **CaptureScreenshotUseCase**
   - Captures screenshots using Steel.dev
   - Stores screenshots locally and/or cloud
   - Associates screenshots with milestones

3. **ScheduleChecksUseCase**
   - Manages cron jobs for periodic checks
   - Configures check frequency per platform

## Infrastructure

### Operators (Strategy Pattern)

Each operator implements the `BaseOperator` interface:

```python
class BaseOperator(ABC):
    @abstractmethod
    async def get_current_stats(self) -> Dict[str, int]:
        """Get current statistics from platform"""
        pass

    @abstractmethod
    async def check_milestones(self, thresholds: List[int]) -> List[Milestone]:
        """Check if any milestones have been reached"""
        pass

    @abstractmethod
    def get_screenshot_url(self, milestone: Milestone) -> str:
        """Get URL to screenshot for milestone"""
        pass
```

### Steel.dev Integration

- Uses Steel Python SDK
- Session management with proper cleanup
- Screenshot capture with retry logic
- Error handling and logging

### Scheduling

- APScheduler for cron-like functionality
- Configurable intervals per platform
- Persistent job storage

## API Layer

### REST API (FastAPI)

Endpoints:
- `POST /api/v1/milestones/check` - Manually trigger milestone check
- `GET /api/v1/milestones` - List captured milestones
- `GET /api/v1/milestones/{id}/screenshot` - Get screenshot
- `POST /api/v1/platforms` - Configure platform
- `GET /api/v1/platforms` - List configured platforms
- `POST /api/v1/schedule` - Configure schedule

## CLI Interface

Commands:
- `fabo check` - Check milestones now
- `fabo configure` - Configure platforms and credentials
- `fabo schedule` - Set up automatic checks
- `fabo list` - List captured milestones
- `fabo serve` - Start API server

## Configuration

### Environment Variables

```
STEEL_API_KEY=your-steel-api-key
GITHUB_TOKEN=your-github-token
TWITTER_BEARER_TOKEN=your-twitter-token
LINKEDIN_ACCESS_TOKEN=your-linkedin-token
DATABASE_URL=sqlite:///fabo.db
LOG_LEVEL=INFO
```

### Configuration File (YAML)

```yaml
platforms:
  github:
    enabled: true
    repositories:
      - owner: nkkko
        name: fabo
    thresholds: [100, 500, 1000, 5000, 10000]
    check_interval: 3600  # seconds

  twitter:
    enabled: true
    username: your_username
    thresholds: [100, 500, 1000, 10000]
    check_interval: 3600

  linkedin:
    enabled: false

screenshots:
  storage_path: ./screenshots
  format: png
  full_page: true

notifications:
  enabled: true
  channels:
    - email
    - slack
```

## Technology Stack

### Core
- **Python**: 3.12+
- **Package Manager**: uv (Astral)
- **Dependency Injection**: dependency-injector

### Infrastructure
- **Browser Automation**: Steel.dev Python SDK
- **HTTP Client**: httpx (async)
- **API Framework**: FastAPI
- **CLI Framework**: Typer
- **Scheduling**: APScheduler
- **Database**: SQLite (default), PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0

### Development
- **Linting**: ruff
- **Formatting**: black
- **Type Checking**: mypy
- **Testing**: pytest, pytest-asyncio
- **Coverage**: pytest-cov

## Design Patterns

1. **Repository Pattern**: Data access abstraction
2. **Strategy Pattern**: Platform operators
3. **Factory Pattern**: Operator creation
4. **Dependency Injection**: Service composition
5. **CQRS**: Separate read/write operations (future)

## Scalability Considerations

1. **Async Operations**: All I/O operations are async
2. **Queue-based Processing**: For high-volume scenarios (future)
3. **Caching**: Redis for API responses (future)
4. **Rate Limiting**: Respect platform API limits
5. **Distributed Scheduling**: When scaling horizontally (future)

## Security

1. **Credential Encryption**: Secrets stored encrypted
2. **API Authentication**: JWT tokens for API
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Pydantic models
5. **Audit Logging**: Track all operations

## Testing Strategy

1. **Unit Tests**: Domain logic, use cases
2. **Integration Tests**: Database, external APIs (mocked)
3. **E2E Tests**: Full workflow testing
4. **Contract Tests**: API contract validation

## Monitoring & Observability

1. **Structured Logging**: JSON logs with context
2. **Metrics**: Prometheus-compatible metrics (future)
3. **Tracing**: OpenTelemetry (future)
4. **Health Checks**: API health endpoints

## Future Enhancements

1. **Web Interface**: React/Vue.js frontend
2. **Real-time Updates**: WebSocket support
3. **Multi-user**: User management and isolation
4. **Cloud Storage**: S3-compatible storage
5. **AI Analysis**: Analyze milestone trends
6. **Social Sharing**: Auto-post milestones
