# Import the cli decorator
import argparse
from typing import Callable


def cli(func: Callable) -> Callable:
    """Decorator for creating a CLI command."""

    def wrapper(*args, **kwargs):
        """Wrapper function to handle CLI command execution."""
        parser = argparse.ArgumentParser(description="Spearmint CLI")
        parser.add_argument(
            "--config",
            "-c",
            type=str,
            help="Path to the configuration file",
            default=None,
        )
        parser.add_argument(
            "--dataset",
            "-d",
            type=str,
            help="Path to the dataset file",
            default=None,
        )

        parsed_args = parser.parse_args(args)
        kwargs["config"] = parsed_args.config
        kwargs["dataset"] = parsed_args.dataset

        return func(*args, **kwargs)

    return wrapper
