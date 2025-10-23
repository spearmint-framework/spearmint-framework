"""Strategy registry for custom strategy registration.

This module provides a global registry for strategy lookup and registration,
enabling user-defined custom strategies.

Acceptance Criteria Reference: Section 2.7 (Strategy Registry)
- Registration API (register, get, list)
- Support for user-provided custom strategy classes
- Built-in strategy pre-registration
"""

from collections.abc import Callable

from .strategies import (
    MultiBranchStrategy,
    RoundRobinStrategy,
    ShadowStrategy,
    Strategy,
)

# Global strategy registry mapping names to factory functions
_STRATEGIES: dict[str, Callable[[], Strategy]] = {}


def register_strategy(name: str, factory: Callable[[], Strategy]) -> None:
    """Register a strategy factory with the given name.

    Args:
        name: Unique name for the strategy
        factory: Callable that returns a Strategy instance

    Raises:
        ValueError: If strategy name already registered
    """
    if name in _STRATEGIES:
        raise ValueError(f"Strategy '{name}' already registered")
    _STRATEGIES[name] = factory


def get_strategy(name: str) -> Strategy:
    """Retrieve a strategy instance by name.

    Args:
        name: Name of the registered strategy

    Returns:
        New Strategy instance from factory

    Raises:
        ValueError: If strategy name not found
    """
    if name not in _STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'")
    return _STRATEGIES[name]()


def list_strategies() -> list[str]:
    """List all registered strategy names.

    Returns:
        List of registered strategy names
    """
    return list(_STRATEGIES.keys())


# Pre-register built-in strategies
register_strategy("round_robin", RoundRobinStrategy)
register_strategy("shadow", ShadowStrategy)
register_strategy("multi_branch", MultiBranchStrategy)


__all__ = ["register_strategy", "get_strategy", "list_strategies"]
