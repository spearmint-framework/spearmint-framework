# Installation

## Requirements

Spearmint requires Python 3.10 or higher.

## Install from PyPI

```bash
pip install spearmint-framework
```

## Install from Source

For development or to use the latest unreleased features:

```bash
git clone https://github.com/spearmint-framework/spearmint-framework.git
cd spearmint-framework
pip install -e ".[dev]"
```

## Using uv (Recommended for Development)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. To install and run with uv:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/spearmint-framework/spearmint-framework.git
cd spearmint-framework

# Run commands with uv
uv run python -m pytest  # Run tests
uv run python cookbook/basic/simple_experiment.py  # Run examples
```

## Verify Installation

Verify your installation by running:

```bash
python -c "import spearmint; print(spearmint.__version__)"
```

## Optional Dependencies

### MLflow Integration

Spearmint integrates with MLflow for experiment tracking:

```bash
pip install mlflow>=3.5.1
```

MLflow is included as a core dependency, but you may want to configure it separately for production use.

### Development Dependencies

For contributing to Spearmint, install development dependencies:

```bash
pip install spearmint-framework[dev]
```

This includes:
- pytest - Testing framework
- pytest-asyncio - Async test support
- pytest-cov - Coverage reporting
- mypy - Static type checking
- ruff - Linting and formatting

## Troubleshooting

### Python Version Issues

If you encounter Python version errors, ensure you're using Python 3.10+:

```bash
python --version
```

### Import Errors

If you get import errors after installation:

1. Check that spearmint-framework is installed:
   ```bash
   pip list | grep spearmint
   ```

2. Ensure you're using the correct Python environment:
   ```bash
   which python
   ```

3. Try reinstalling:
   ```bash
   pip uninstall spearmint-framework
   pip install spearmint-framework
   ```

## Next Steps

- [Quick Start Guide](quickstart.md) - Build your first experiment
- [Core Concepts](concepts.md) - Learn about configurations and strategies
- [Cookbook](../../cookbook/README.md) - Explore example code
