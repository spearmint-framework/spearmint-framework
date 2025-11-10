from .core import (
    Branch,
    BranchStrategy,
    BranchExecType,
    Config,
    Spearmint,
    experiment_decorator as experiment,
    configure_decorator as configure, 

)

__version__ = "0.3.0"


__all__ = [
    "__version__",
    "Config",
    "Branch",
    "BranchExecType",
    "BranchStrategy",
    "Spearmint",
    "experiment",
    "configure",
]
