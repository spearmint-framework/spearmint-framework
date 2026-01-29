from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from .config import Config
from .dynamic_value import DynamicValue

class Bind:
    """Class to indicate binding of configuration models to function parameters."""

    def __init__(self, path: str) -> None:
        """Initialize a new Bind instance."""
        self.path = path


def parse_configs(
    configs: Sequence[Any], config_handler: Callable[[str | Path], list[dict[str, Any]]]
) -> list[Config]:
    """
    Manually set configurations.

    Args:
        *args: Variable number of configuration dictionaries.
    """
    result = []
    for cfg in configs:
        if isinstance(cfg, BaseModel):
            result.append(Config(cfg.model_dump()))
        elif isinstance(cfg, dict):
            result.extend(generate_configurations(cfg))
        elif isinstance(cfg, str) or isinstance(cfg, Path):
            loaded_configs = config_handler(cfg)
            result.extend([Config(loaded_cfg) for loaded_cfg in loaded_configs])
    return result


def generate_configurations(config: dict[str, Any]) -> list[Config]:
    """Generate configurations for the experiment based on the provided config.

    Args:
        config: Configuration parameters

    Returns:
        List of generated configurations
    """
    dynamic_value_maps = _find_dynamic_values(config)
    values = []
    configurations = []

    for dynamic_value_mapping in dynamic_value_maps:
        value_iterable = dynamic_value_mapping["dynamic_value"]
        values.append(
            [{"keys": dynamic_value_mapping["parent_keys"], "value": val} for val in value_iterable]
        )

    # use itertools to generate all combinations of the sweeper values
    for combo in itertools.product(*values):
        config_copy = deepcopy(config)
        for item in combo:
            keys = item["keys"]
            value = item["value"]
            # Traverse the config dictionary to set the value
            d = config_copy
            for key in keys[:-1]:
                d = d.setdefault(key, {})
            d[keys[-1]] = value
        configurations.append(Config(config_copy))

    return configurations


def _find_dynamic_values(
    config: dict[str, Any], parent_keys: list[str] = []
) -> list[dict[str, Any]]:
    """Find all dynamic_values in the configuration.

    Args:
        config: Configuration parameters

    Returns:
        List of found dynamic_values
    """
    dynamic_values = []
    for key, value in config.items():
        if isinstance(value, DynamicValue):
            p_keys = parent_keys.copy()
            p_keys.append(key)
            dynamic_values.append({"dynamic_value": value, "parent_keys": p_keys})
        elif isinstance(value, dict):
            nested_dynamic_values = _find_dynamic_values(value, parent_keys + [key])
            if nested_dynamic_values:
                dynamic_values.extend(nested_dynamic_values)

    return dynamic_values


__all__ = ["Config", "DynamicValue", "generate_configurations", "parse_configs"]
