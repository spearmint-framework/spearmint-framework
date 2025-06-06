# Import the cli decorator
from typing import Callable
import argparse

from .hypothesis import Hypothesis


def cli(func: Callable, hypothesis: Hypothesis) -> Callable:
    """Decorator for creating a CLI command."""
    
    def wrapper(*args, **kwargs):
        """Wrapper function to handle CLI command execution."""
        parser = argparse.ArgumentParser(description="Spearmint CLI")
        parser.add_argument("experiment", type=str, help="Name of the experiment to run")
        parser.add_argument("--config", type=str, help="Path to the configuration file", default=None)
        parsed_args = parser.parse_args(args)
        kwargs['experiment'] = parsed_args.experiment
        kwargs['config'] = parsed_args.config

        return func(*args, **kwargs)
    
    return wrapper