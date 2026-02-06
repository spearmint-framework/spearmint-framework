# Contributing to Spearmint

Thank you for your interest in contributing to Spearmint! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building a welcoming community.

## Quick Start

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/spearmint-framework.git
cd spearmint-framework
```

### 2. Set Up Development Environment

We recommend using [uv](https://github.com/astral-sh/uv) for development:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# No additional setup needed - uv handles everything!
```

Alternatively, use pip:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Run Tests

```bash
# With uv (recommended)
uv run python -m pytest

# With pip
pytest
```

### 4. Make Changes

Create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

### 5. Submit Pull Request

Push your changes and open a pull request on GitHub.

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run python -m pytest

# Run specific test file
uv run python -m pytest src/tests/test_spearmint.py

# Run with coverage
uv run python -m pytest --cov=src --cov-report=html
```

### Code Quality

We use several tools to maintain code quality:

#### Linting with Ruff

```bash
# Check code
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/
```

#### Type Checking with mypy

```bash
uv run mypy src/spearmint/
```

#### Format Code

```bash
# Format with ruff
uv run ruff format src/
```

### Running Examples

Test your changes with cookbook examples:

```bash
uv run python cookbook/basic/simple_experiment.py
uv run python cookbook/configuration/typed_config.py
```

## Project Structure

```
spearmint-framework/
├── src/
│   ├── spearmint/           # Main package
│   │   ├── __init__.py
│   │   ├── spearmint.py     # Core Spearmint class
│   │   ├── configuration/   # Configuration management
│   │   ├── context.py       # Execution context
│   │   ├── experiment_function.py  # Experiment wrapper
│   │   ├── registry.py      # Global registry
│   │   ├── runner.py        # Execution runtime
│   │   └── utils/           # Utilities
│   └── tests/               # Test suite
├── cookbook/                # Example code
├── docs/                    # Documentation
├── pyproject.toml           # Project configuration
└── uv.lock                  # Dependency lock file
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all functions
- Maximum line length: 100 characters
- Use descriptive variable names

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Type Hints

Always include type hints:

```python
def process_config(config: dict[str, Any], flag: bool = False) -> list[Config]:
    """Process configuration with optional flag."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> dict[str, Any]:
    """One-line summary.

    More detailed description if needed. Explain what the function does,
    not how it does it.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param2 is negative.

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'status': 'success'}
    """
    ...
```

## Testing Guidelines

### Writing Tests

- Place tests in `src/tests/`
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names

```python
def test_spearmint_injects_config_correctly():
    """Test that config is properly injected into experiment function."""
    mint = Spearmint(configs=[{"key": "value"}])
    
    @mint.experiment()
    def func(config: dict) -> str:
        return config["key"]
    
    result = func()
    assert result == "value"
```

### Test Coverage

- Aim for >80% test coverage
- Test edge cases and error conditions
- Test both sync and async code paths

### Async Tests

Use `pytest-asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_experiment():
    """Test async experiment execution."""
    mint = Spearmint(configs=[{"model": "gpt-4"}])
    
    @mint.experiment()
    async def async_func(config: dict) -> str:
        return config["model"]
    
    result = await async_func()
    assert result == "gpt-4"
```

## Documentation

### Updating Documentation

When adding features:

1. Update relevant docs in `docs/`
2. Add examples to `cookbook/`
3. Update `README.md` if needed
4. Add docstrings to new functions/classes

### Documentation Style

- Write in present tense
- Be concise and clear
- Include code examples
- Follow the [Diátaxis framework](https://diataxis.fr/):
  - **Tutorials**: Learning-oriented
  - **How-to guides**: Problem-oriented
  - **Reference**: Information-oriented
  - **Explanation**: Understanding-oriented

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code follows style guidelines (ruff)
- [ ] Type hints are correct (mypy)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Changelog entry added (if applicable)

### PR Guidelines

1. **Title**: Use descriptive title
   - Good: "Add support for nested DynamicValue expansion"
   - Bad: "Fix bug"

2. **Description**: Explain:
   - What changes were made
   - Why they were needed
   - How to test the changes

3. **Small PRs**: Keep PRs focused and small
   - Easier to review
   - Faster to merge
   - Less likely to have conflicts

4. **Tests**: Include tests with your changes

### PR Template

```markdown
## Description
Brief description of changes.

## Motivation
Why are these changes needed?

## Changes
- List of changes made

## Testing
How to test these changes?

## Checklist
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] Changelog updated
```

## Common Tasks

### Adding a New Feature

1. Create a branch: `git checkout -b feature/my-feature`
2. Write tests first (TDD approach)
3. Implement the feature
4. Update documentation
5. Run tests and linting
6. Submit PR

### Fixing a Bug

1. Create a branch: `git checkout -b fix/bug-description`
2. Write a failing test that reproduces the bug
3. Fix the bug
4. Verify test passes
5. Submit PR

### Improving Documentation

1. Create a branch: `git checkout -b docs/improvement-description`
2. Make documentation changes
3. Preview changes locally
4. Submit PR

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/spearmint-framework/spearmint-framework/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/spearmint-framework/spearmint-framework/issues)
- **Ideas**: Start a discussion or open an issue with the "enhancement" label

## Known Issues

See the [.project/tasks/](../.project/tasks/) directory for known technical debt and improvement opportunities.

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag: `git tag v0.x.x`
4. Push tag: `git push origin v0.x.x`
5. GitHub Actions will publish to PyPI

## Code Review Guidelines

### For Contributors

- Be responsive to feedback
- Don't take criticism personally
- Ask questions if feedback is unclear

### For Reviewers

- Be constructive and respectful
- Explain why changes are needed
- Approve when ready, don't nitpick

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions make Spearmint better for everyone. Thank you for being part of the community! 🌱
