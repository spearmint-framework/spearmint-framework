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

from .multi_branch import MultiBranchStrategy
from .round_robin import RoundRobinBranchStrategy
from .shadow import ShadowBranchStrategy
from .default import DefaultBranchStrategy
from .random import RandomBranchStrategy

__all__ = [
    "RoundRobinBranchStrategy",
    "ShadowBranchStrategy",
    "MultiBranchStrategy",
    "DefaultBranchStrategy",
    "RandomBranchStrategy",
]
