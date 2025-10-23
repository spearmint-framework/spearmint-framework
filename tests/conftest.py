"""Pytest configuration and shared fixtures for spearmint tests."""

import pytest


@pytest.fixture
def event_loop_policy() -> None:
    """Fixture for event loop policy if needed for async tests."""
    # Placeholder for future async test configuration
    pass


@pytest.fixture
def in_memory_logger() -> None:
    """Fixture providing an in-memory logger for testing.

    TODO: Implement once logging.InMemoryLogger is available.
    """
    pass
