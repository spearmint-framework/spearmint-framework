"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

from .core import Spearmint
from .components import prompt_from_file, structured_chat_completion
from .sweepers import RangeSweeper, ListSweeper

# Create an instance of the Spearmint class when imported
sm = Spearmint()

# Re-export key decorators and methods at the module level for convenience
register_experiment = sm.register_experiment
hypothesis = sm.hypothesis
factor = sm.factor
run = sm.run
list = ListSweeper()
range = RangeSweeper()

# Export all public components
__all__ = [
    'sm',
    'register_experiment',
    'hypothesis',
    'factor',
    'run',
    'list',
    'range',
    'prompt_from_file',
    'structured_chat_completion',
]
