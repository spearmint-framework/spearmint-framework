"""Smoke tests for module imports and basic functionality."""


def test_import_spearmint() -> None:
    """Test that spearmint root module can be imported."""
    import spearmint

    assert spearmint is not None


def test_spearmint_version() -> None:
    """Test that __version__ is accessible."""
    import spearmint

    assert hasattr(spearmint, "__version__")
    assert isinstance(spearmint.__version__, str)
    assert spearmint.__version__ == "0.1.0"


def test_import_branch_module() -> None:
    """Test that branch module can be imported."""
    from spearmint import branch

    assert branch is not None


def test_import_strategies_module() -> None:
    """Test that strategies module can be imported."""
    from spearmint import strategies

    assert strategies is not None


def test_import_logging_module() -> None:
    """Test that logging module can be imported without MLflow installed."""
    from spearmint import logging

    assert logging is not None


def test_import_config_module() -> None:
    """Test that config module can be imported."""
    from spearmint import config

    assert config is not None
