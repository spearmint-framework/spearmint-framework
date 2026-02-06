# Contributing to Spearmint

Thank you for your interest in contributing to Spearmint! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions. We're building a welcoming community.

---

## Ways to Contribute

- **Report bugs**: Open issues for bugs you discover
- **Suggest features**: Share ideas for new functionality
- **Improve documentation**: Fix typos, clarify explanations, add examples
- **Submit code**: Fix bugs or implement features
- **Write tests**: Improve test coverage
- **Review PRs**: Help review others' contributions

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Clone the Repository

``````bash
git clone https://github.com/spearmint-framework/spearmint-framework.git
cd spearmint-framework
``````

### Install Dependencies

Using uv (recommended):

``````bash
uv sync --dev
``````

Using pip:

``````bash
pip install -e ".[dev]"
``````

### Verify Setup

Run tests to ensure everything works:

``````bash
uv run python -m pytest
``````

---

## Development Workflow

### 1. Create a Branch

``````bash
git checkout -b feature/your-feature-name
``````

Use prefixes:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

Follow the coding standards below and write tests for new functionality.

### 3. Run Tests

``````bash
# Run all tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=src --cov-report=html

# Run specific test file
uv run python -m pytest tests/test_spearmint.py
``````

### 4. Run Linters

``````bash
# Check formatting and linting
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/
``````

### 5. Type Check

``````bash
uv run mypy src/spearmint
``````

### 6. Commit Changes

Write clear, descriptive commit messages:

``````bash
git add .
git commit -m "Add feature: multi-config selection strategy"
``````

**Good commit messages:**
- Start with a verb (Add, Fix, Update, Remove)
- Be specific about what changed
- Reference issue numbers when applicable

**Examples:**
- ✅ `Fix: Prevent race condition in async runner`
- ✅ `Add: Support for custom config ID generation`
- ✅ `Docs: Clarify DynamicValue usage in README`
- ❌ `Fixed stuff`
- ❌ `Update`

### 7. Push and Create PR

``````bash
git push origin feature/your-feature-name
``````

Then open a Pull Request on GitHub with:
- Clear description of changes
- Link to related issue (if any)
- Screenshots (for UI/documentation changes)
- Checklist of what was done

---

## Coding Standards

### Python Style

Follow [PEP 8](https://peps.python.org/pep-0008/) and use type hints:

``````python
def process_config(config: dict[str, Any]) -> Config:
    """Process a configuration dictionary.
    
    Args:
        config: Raw configuration dictionary
        
    Returns:
        Processed Config object
    """
    return Config(config)
``````

### Type Hints

Use type hints for all functions:

``````python
from typing import Any

def my_function(param: str, count: int = 1) -> list[str]:
    return [param] * count
``````

### Docstrings

Use Google-style docstrings:

``````python
def calculate_score(predictions: list[float], targets: list[float]) -> float:
    """Calculate accuracy score.
    
    Args:
        predictions: List of predicted values
        targets: List of target values
        
    Returns:
        Accuracy score between 0.0 and 1.0
        
    Raises:
        ValueError: If lists have different lengths
    """
    if len(predictions) != len(targets):
        raise ValueError("Length mismatch")
    return sum(p == t for p, t in zip(predictions, targets)) / len(targets)
``````

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `ConfigHandler`)
- **Functions/methods**: `snake_case` (e.g., `parse_config`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- **Private methods**: `_leading_underscore` (e.g., `_internal_helper`)

---

## Testing Guidelines

### Writing Tests

Use pytest for testing:

``````python
def test_config_parsing():
    """Test that configs are parsed correctly."""
    config = {"model": "gpt-4", "temperature": 0.7}
    parsed = parse_configs([config])
    
    assert len(parsed) == 1
    assert parsed[0]["model"] == "gpt-4"
    assert parsed[0]["temperature"] == 0.7
``````

### Test Organization

- Place tests in `tests/` directory
- Mirror source structure (e.g., `tests/test_config.py` for `src/spearmint/config.py`)
- Use descriptive test names: `test_dynamic_value_expands_correctly`

### Async Tests

Use `pytest-asyncio` for async tests:

``````python
import pytest

@pytest.mark.asyncio
async def test_async_runner():
    """Test async experiment execution."""
    @mint.experiment()
    async def async_func(x: int, config: Config) -> int:
        return x * 2
    
    async with Spearmint.arun(async_func) as runner:
        result = await runner(5)
        assert result.main_result.result == 10
``````

### Coverage

Aim for high test coverage:
- New features should have >90% coverage
- Bug fixes should include regression tests
- Edge cases should be tested

---

## Documentation Guidelines

### Code Comments

Comment **why**, not **what**:

``````python
# ✅ Good - explains reasoning
# Use SHA256 to ensure consistent IDs across runs
config_id = hashlib.sha256(config_str.encode()).hexdigest()

# ❌ Bad - states the obvious
# Hash the config string
config_id = hashlib.sha256(config_str.encode()).hexdigest()
``````

### Documentation Files

- Use Markdown (`.md`) format
- Follow [Diátaxis framework](https://diataxis.fr/)
- Include code examples
- Test code examples to ensure they work

### README Updates

Update README.md if you:
- Add new public APIs
- Change core functionality
- Add major features

---

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted with Ruff
- [ ] Type checks pass with mypy
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)

### PR Description Template

``````markdown
## Description
Brief description of changes

## Related Issues
Fixes #123

## Changes Made
- Added X feature
- Updated Y documentation
- Fixed Z bug

## Testing
- [ ] Added unit tests
- [ ] Tested manually
- [ ] Updated integration tests

## Screenshots (if applicable)
[Add screenshots for UI/docs changes]
``````

### Review Process

1. **Automated checks**: CI runs tests, linters, type checks
2. **Maintainer review**: A maintainer will review your PR
3. **Address feedback**: Make requested changes
4. **Merge**: Once approved, maintainer will merge

---

## Project Structure

``````
spearmint-framework/
├── src/spearmint/              # Main source code
│   ├── __init__.py
│   ├── spearmint.py            # Core Spearmint class
│   ├── experiment_function.py  # Function decorator logic
│   ├── runner.py               # Execution runners
│   ├── context.py              # Context management
│   ├── registry.py             # Function registry
│   ├── configuration/          # Config system
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── dynamic_value.py
│   └── utils/                  # Utilities
│       ├── __init__.py
│       └── handlers.py
├── tests/                      # Test files
│   ├── __init__.py
│   └── test_spearmint.py
├── cookbook/                   # Example code
│   ├── basic/
│   ├── advanced/
│   └── online_experiments/
├── docs/                       # Documentation
│   ├── index.md
│   ├── tutorials/
│   ├── how-to/
│   ├── reference/
│   └── explanation/
├── pyproject.toml              # Project metadata
└── README.md                   # Main README
``````

---

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag: `git tag v0.2.2`
4. Push tag: `git push origin v0.2.2`
5. GitHub Actions builds and publishes to PyPI

---

## Getting Help

- **GitHub Discussions**: Ask questions, share ideas
- **GitHub Issues**: Report bugs, request features
- **Pull Requests**: Get feedback on code

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- GitHub contributor graph

Thank you for contributing to Spearmint! 🌱
