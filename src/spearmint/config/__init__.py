"""Strategy package aggregating all built-in strategy implementations.

Public API:
    - Strategy (Protocol)
    - RoundRobinStrategy
    - ShadowStrategy
    - MultiBranchStrategy

The unified import path remains `from spearmint.strategies import X` for
backward compatibility.
"""

from __future__ import annotations

from .config import Config
from .dynamic_value import DynamicValue, generate_configurations

__all__ = [
    "Config",
    "DynamicValue",
    "generate_configurations",
]
