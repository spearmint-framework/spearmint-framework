"""Pytest configuration and shared fixtures for spearmint tests."""

import pytest


@pytest.fixture
def event_loop_policy() -> None:
    """Fixture for event loop policy if needed for async tests."""
    # Placeholder for future async test configuration
    pass


@pytest.fixture
def sample_configs() -> list[dict[str, int]]:
    """Fixture providing sample configuration dictionaries."""
    return [
        {"delta": 1, "multiplier": 2},
        {"delta": 5, "multiplier": 3},
        {"delta": 10, "multiplier": 1},
    ]


@pytest.fixture
def single_config() -> list[dict[str, int]]:
    """Fixture providing a single configuration."""
    return [{"delta": 5, "multiplier": 2}]


@pytest.fixture
async def sample_async_func():
    """Fixture providing a simple async test function."""

    async def func(x: int, config: dict) -> int:
        """Sample function that adds config delta to x."""
        return x + config.get("delta", 0)

    return func


@pytest.fixture
async def failing_async_func():
    """Fixture providing an async function that fails based on config."""

    async def func(x: int, config: dict) -> int:
        """Sample function that raises if config has 'should_fail' key."""
        if config.get("should_fail", False):
            raise ValueError(f"Intentional failure with delta {config.get('delta', 0)}")
        return x + config.get("delta", 0)

    return func
