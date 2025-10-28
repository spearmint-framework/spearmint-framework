import itertools
from collections.abc import Iterable
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class DynamicValue(Generic[T]):
    """
    DynamicValue class that represents a value that can be dynamically generated.

    This class is used to indicate that a value should be generated at runtime,
    rather than being statically defined in the configuration.

    Type Parameters:
        T: The type of the value held by this DynamicValue instance.
    """

    def __init__(self, values: Iterable[T]) -> None:
        """Initialize a new DynamicValue instance."""
        self.values: Iterable[T] = values

    def __repr__(self) -> str:
        """Return a string representation of the DynamicValue."""
        return f"DynamicValue({self.values})"

    def __iter__(self) -> Iterable[T]:
        """Return an iterator over the values."""
        return iter(self.values)


def _generate_configurations(config: dict[str, Any]) -> list[dict[str, Any]]:
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
        config_copy = config.copy()
        for item in combo:
            keys = item["keys"]
            value = item["value"]
            # Traverse the config dictionary to set the value
            d = config_copy
            for key in keys[:-1]:
                d = d.setdefault(key, {})
            d[keys[-1]] = value
        configurations.append(config_copy)

    return configurations


def _find_dynamic_values(config: dict[str, Any], parent_keys: list = []) -> list[dict[str, Any]]:
    """Find all dynamic_values in the configuration.

    Args:
        config: Configuration parameters

    Returns:
        List of found dynamic_values
    """
    dynamic_values = []
    for key, value in config.items():
        if isinstance(value, DynamicValue):
            keys = [key]
            keys.extend(parent_keys)
            dynamic_values.append({"dynamic_value": value, "parent_keys": keys})
        elif isinstance(value, dict):
            parent_keys.append(key)
            nested_dynamic_values = _find_dynamic_values(value, parent_keys)
            if nested_dynamic_values:
                dynamic_values.extend(nested_dynamic_values)

    return dynamic_values
