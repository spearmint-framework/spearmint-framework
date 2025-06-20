"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

from  .cli import cli
from .config import DynamicValue
from .experiment import Experiment
from .hypothesis import Hypothesis

# instantiate the Hypothesis class so it can be used like
# `import spearmint as mint`

hypothesis = Hypothesis()

# alias hypothesis properties for convenience

configure = hypothesis.configure
add_service = hypothesis.add_service
run = hypothesis.run
load_dataset = hypothesis.load_dataset
inputs = hypothesis.inputs
add_evaluator = hypothesis.add_evaluator

# TODO - register other functions as configurable
# configurable = hypothesis.configurable

# Decorators
add_experiment = hypothesis.experiment_fn_decorator

vary = DynamicValue

# Export all public components
__all__ = [
    "Hypothesis",
    "Experiment",
    "cli",
]
