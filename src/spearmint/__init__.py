"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

from  .cli import cli
from .experiment import Experiment, experiment
from .hypothesis import Hypothesis


# Export all public components
__all__ = [
    "Hypothesis",
    "Experiment",
    "cli",
    "experiment",
]
