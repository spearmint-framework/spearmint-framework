"""Type definitions for the Spearmint framework.

A root-level types.py file (at the package level) is most commonly used as a
centralized location for shared type definitions that are used across multiple
modules within the package.

Typical contents include:
Type aliases - Creating readable names for complex types (e.g., UserId = int, JSONDict = dict[str, Any])
TypedDict classes - Defining structured dictionary schemas (like your ExceptionInfo)
Literal types - Defining valid string/value constants (like your Status)
Protocol classes - Defining structural interfaces for duck typing
Generic type variables - Shared TypeVar definitions used across the package
Union types and common combinations - Complex types used in multiple places

The pattern you're using in spearmint follows this convention well - you have
a Status literal type and an ExceptionInfo TypedDict that are likely imported
and used by multiple modules throughout the package (like branch.py, experiment.py,
etc.). This avoids circular imports and provides a single source of truth for
these type definitions.
"""

from typing import Literal, TypedDict

# Status literals for branch execution state
Status = Literal["pending", "success", "failed", "skipped"]
STATUSES = {"pending", "success", "failed", "skipped"}


class ExceptionInfo(TypedDict):
    """Structure for capturing exception details."""

    type: str
    message: str
    traceback: str
