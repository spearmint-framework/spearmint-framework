from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BranchScope:
    branch: "Branch | None" = None
    data: dict[str, Any] = field(default_factory=dict)
    parent: "BranchScope | None" = None
    children: list["BranchScope"] = field(default_factory=list)


class RootScope(BranchScope):
    def __init__(self) -> None:
        super().__init__(branch=None, parent=None)


current_scope: ContextVar[BranchScope] = ContextVar("spearmint_branch_scope", default=RootScope())
