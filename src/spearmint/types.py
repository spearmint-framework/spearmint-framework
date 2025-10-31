"""Type definitions for the Spearmint framework."""

from typing import Literal, TypedDict

# Status literals for branch execution state
Status = Literal["pending", "success", "failed", "skipped"]
STATUSES = {"pending", "success", "failed", "skipped"}


class ExceptionInfo(TypedDict):
    """Structure for capturing exception details."""

    type: str
    message: str
    traceback: str
