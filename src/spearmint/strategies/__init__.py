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

from .base import Strategy
from .multi_branch import MultiBranchStrategy
from .round_robin import RoundRobinStrategy
from .shadow import ShadowStrategy
from .single_config import SingleConfigStrategy

__all__ = [
    "Strategy",
    "RoundRobinStrategy",
    "ShadowStrategy",
    "MultiBranchStrategy",
    "SingleConfigStrategy",
]
