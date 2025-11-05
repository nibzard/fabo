# Contributing to FABO

Thank you for your interest in contributing to FABO! We welcome contributions from the community.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Adding New Operators](#adding-new-operators)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fabo.git
   cd fabo
   ```

3. **Install dependencies**:
   ```bash
   uv sync --extra dev
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

## Development Setup

### Prerequisites

- Python 3.12+
- uv package manager
- Git

### Installation

```bash
# Install with dev dependencies
uv sync --extra dev

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

### Environment

Copy `.env.example` to `.env` and configure your API keys for testing:

```bash
cp .env.example .env
# Edit .env with your test credentials
```

## Project Structure

FABO follows Domain-Driven Design (DDD):

```
src/fabo/
├── domain/              # Core business logic
│   ├── entities/        # Business entities (Milestone, Platform, etc.)
│   ├── value_objects/   # Immutable value objects
│   ├── repositories/    # Repository interfaces
│   └── services/        # Domain services
│
├── application/         # Use cases and orchestration
│   ├── use_cases/       # Application use cases
│   └── dtos/           # Data Transfer Objects
│
├── infrastructure/      # External integrations
│   ├── operators/       # Platform operators (GitHub, Twitter, etc.)
│   ├── llm/            # LLM vision services
│   ├── screenshot/      # Steel.dev integration
│   ├── persistence/     # State management
│   └── config/         # Configuration
│
└── interfaces/         # User interfaces
    ├── cli/            # Command-line interface
    └── api/            # REST API (future)
```

## Making Changes

### 1. Choose What to Work On

- Check the [issues](https://github.com/nkkko/fabo/issues) for things to work on
- Comment on an issue to let others know you're working on it
- For new features, open an issue first to discuss

### 2. Write Code

Follow the existing code patterns:

- **Type hints**: Use full type hints for all functions
- **Docstrings**: Document all public functions and classes
- **Async**: Use async/await for I/O operations
- **Logging**: Use structured logging with `structlog`

Example:

```python
async def my_function(param: str) -> dict[str, Any]:
    """Do something useful.

    Args:
        param: Description of parameter.

    Returns:
        Dictionary with results.

    Raises:
        ValueError: If param is invalid.
    """
    logger.info("doing_something", param=param)
    # Implementation
    return {"result": "success"}
```

### 3. Test Your Changes

```bash
# Run tests
pytest

# Run specific test
pytest tests/unit/test_operators.py

# Run with coverage
pytest --cov=src/fabo --cov-report=html

# Type check
mypy src/

# Lint
ruff check src/

# Format
black src/
```

## Adding New Operators

To add support for a new platform:

### 1. Add Milestone Types

Edit `src/fabo/domain/value_objects/milestone_type.py`:

```python
class MilestoneType(str, Enum):
    # ... existing types ...

    # YouTube milestones
    YOUTUBE_SUBSCRIBERS = "youtube_subscribers"
    YOUTUBE_VIEWS = "youtube_views"
```

### 2. Create Operator Class

Create `src/fabo/infrastructure/operators/youtube_operator.py`:

```python
from fabo.infrastructure.operators.base_operator import BaseOperator
from fabo.domain.value_objects.milestone_type import MilestoneType

class YouTubeOperator(BaseOperator):
    """Operator for YouTube platform."""

    async def validate_credentials(self) -> bool:
        # Validate YouTube API key
        pass

    async def get_current_stats(self) -> dict[MilestoneType, int]:
        # Fetch current metrics
        pass

    def get_screenshot_url(self, milestone: Milestone) -> str:
        # Return channel URL
        pass
```

### 3. Register in Factory

Edit `src/fabo/infrastructure/operators/factory.py`:

```python
from fabo.infrastructure.operators.youtube_operator import YouTubeOperator

def create_operator(platform_config: Platform) -> BaseOperator:
    operators = {
        # ... existing ...
        PlatformType.YOUTUBE: YouTubeOperator,
    }
    # ...
```

### 4. Add LLM Vision Support

Edit `src/fabo/infrastructure/llm/vision_service.py`:

```python
async def analyze_youtube_screenshot(
    self, screenshot_path: Path, expected_channel: str | None = None
) -> MetricExtraction:
    """Analyze a YouTube channel screenshot."""
    prompt = """Analyze this YouTube channel page..."""
    return await self._analyze_screenshot(screenshot_path, prompt, "subscribers")
```

### 5. Create Example Config

Create `runs/example-youtube-subscribers.yaml`:

```yaml
id: youtube-mychannel-subscribers
platform: youtube
target:
  channel_id: your-channel-id
metrics:
  - type: subscribers
    thresholds: [100, 1000, 10000, 100000]
```

### 6. Document

Add documentation in `docs/operators.md` for your new operator.

### 7. Test

Create tests in `tests/unit/test_youtube_operator.py`.

## Testing

### Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_operators.py
import pytest
from fabo.infrastructure.operators.github_operator import GitHubOperator

@pytest.mark.asyncio
async def test_github_operator_validation(mock_platform_config):
    operator = GitHubOperator(mock_platform_config)
    is_valid = await operator.validate_credentials()
    assert is_valid
```

### Integration Tests

Test interactions between components:

```python
# tests/integration/test_smart_operator.py
@pytest.mark.asyncio
async def test_smart_operator_mode_switching(run_config, state_manager):
    # Test mode switching logic
    pass
```

### Testing with Real APIs

When testing with real APIs:
- Use your own test accounts
- Set appropriate rate limits
- Clean up test data
- Don't commit API keys

## Code Style

### Python

- **Formatter**: Black with 100 character line length
- **Linter**: Ruff with recommended rules
- **Type checker**: mypy in strict mode

```bash
# Format code
black src/

# Check style
ruff check src/

# Fix auto-fixable issues
ruff check --fix src/

# Type check
mypy src/
```

### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Examples:

```bash
git commit -m "feat: add YouTube operator support"
git commit -m "fix: handle rate limits in GitHub operator"
git commit -m "docs: update operator development guide"
```

## Submitting Changes

### 1. Ensure Quality

Before submitting:

- [ ] All tests pass
- [ ] Code is formatted with Black
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Documentation is updated
- [ ] CHANGELOG is updated (if applicable)

### 2. Push Your Branch

```bash
git push origin feature/my-new-feature
```

### 3. Create Pull Request

1. Go to [GitHub](https://github.com/nkkko/fabo/pulls)
2. Click "New Pull Request"
3. Select your branch
4. Fill in the PR template:
   - Description of changes
   - Related issues
   - Testing done
   - Screenshots (if UI changes)

### 4. Code Review

- Address review comments
- Push updates to your branch
- PR will be merged when approved

## Development Tips

### Quick Testing

```bash
# Test a specific operator
fabo run --config runs/example-github-stars.yaml --dry-run

# Test with verbose output
fabo run --config runs/test.yaml --verbose

# Force screenshot mode to test LLM
fabo run --config runs/test.yaml --force-screenshot
```

### Debugging

Use structured logging:

```python
logger.debug("debugging_info", variable=value, state=current_state)
logger.info("action_started", action="check_milestones")
logger.warning("potential_issue", issue="low_confidence")
logger.error("operation_failed", error=str(e))
```

### Testing LLM Vision

To test LLM vision without running full checks:

```python
from fabo.infrastructure.llm.vision_service import VisionService

async def test_vision():
    vision = VisionService(provider="anthropic", api_key="...")
    result = await vision.analyze_github_screenshot(Path("screenshot.png"))
    print(result.metric_value, result.confidence)
```

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/nkkko/fabo/discussions)
- **Bugs**: Open an [Issue](https://github.com/nkkko/fabo/issues)
- **Chat**: (Future: Discord/Slack link)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to FABO! 🎉
