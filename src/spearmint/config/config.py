"""Configuration management utilities.

This module provides utilities for loading, expanding, and managing experiment
configurations from YAML files and Pydantic models.

Acceptance Criteria Reference: Section 4 (Configuration Management)
- YAML base set loaded from directory/direct file(s)
- Pydantic model with custom expansion types for programmatic variant generation
- Merging precedence: Programmatic expansions override or extend the base set
- Each final Config has a stable config_id (hash of normalized content or user-provided field)
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict


class Config(BaseModel):
    model_config = ConfigDict(extra="allow")


def generate_config_id(config: dict[str, Any]) -> str:
    """Generate a stable, deterministic config ID from configuration content.

    Uses SHA256 hash of the normalized (sorted) JSON representation of the config.
    If the config contains a 'config_id' field, that is used instead.

    Args:
        config: Configuration dictionary

    Returns:
        Stable config ID string (either from config['config_id'] or computed hash)
    """
    # If config explicitly provides config_id, use it
    if "config_id" in config:
        return str(config["config_id"])

    # Otherwise, compute hash from normalized content
    # Sort keys for deterministic ordering
    normalized = json.dumps(config, sort_keys=True, default=str)
    hash_obj = hashlib.sha256(normalized.encode("utf-8"))
    return hash_obj.hexdigest()[:16]  # Use first 16 chars for brevity


def load_configs_from_yaml(path: str | Path, validate: bool = True) -> list[dict[str, Any]]:
    """Load configurations from YAML file(s).

    Supports both single file and directory paths. When given a directory,
    loads all .yaml and .yml files recursively.

    Args:
        path: Path to YAML file or directory containing YAML files
        validate: If True, validate that configs are properly formatted dicts

    Returns:
        List of configuration dictionaries

    Raises:
        FileNotFoundError: If path does not exist
        ValueError: If YAML is malformed or validation fails
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"Configuration path does not exist: {path}")

    configs: list[dict[str, Any]] = []

    if path_obj.is_file():
        configs.extend(_load_yaml_file(path_obj, validate))
    elif path_obj.is_dir():
        # Load all YAML files in directory (recursively)
        for yaml_file in sorted(path_obj.rglob("*.yaml")) + sorted(path_obj.rglob("*.yml")):
            configs.extend(_load_yaml_file(yaml_file, validate))
    else:
        raise ValueError(f"Path is neither file nor directory: {path}")

    return configs


def _load_yaml_file(file_path: Path, validate: bool) -> list[dict[str, Any]]:
    """Load configurations from a single YAML file.

    Supports both single config (dict) and multiple configs (list of dicts).

    Args:
        file_path: Path to YAML file
        validate: If True, validate config structure

    Returns:
        List of configuration dictionaries

    Raises:
        ValueError: If YAML content is invalid or validation fails
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML file {file_path}: {e}") from e

    # Handle empty files
    if content is None:
        return []

    # Normalize to list
    if isinstance(content, dict):
        configs = [content]
    elif isinstance(content, list):
        configs = content
    else:
        raise ValueError(
            f"YAML file {file_path} must contain a dict or list of dicts, "
            f"got {type(content).__name__}"
        )

    if validate:
        for i, config in enumerate(configs):
            if not isinstance(config, dict):
                raise ValueError(
                    f"Config at index {i} in {file_path} must be a dict, "
                    f"got {type(config).__name__}"
                )

    return configs


def expand_configs_from_model(
    model: BaseModel, base_configs: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Expand configurations using Pydantic model.

    Converts a Pydantic model instance to a configuration dictionary and optionally
    merges with or extends a base set of configurations. This enables programmatic
    generation of config variants (e.g., Cartesian product, random draws).

    Merging precedence: Model-based expansions override or extend the base set.

    Args:
        model: Pydantic model instance representing a config or config expansion
        base_configs: Optional base configurations to merge with or extend

    Returns:
        List of expanded configuration dictionaries with generated config_ids
    """
    # Convert model to dict
    model_dict = model.model_dump()

    # If no base configs, return model as single config
    if base_configs is None or len(base_configs) == 0:
        config = _ensure_config_id(model_dict)
        return [config]

    # Merge model dict with each base config (model overrides base)
    expanded = []
    for base_config in base_configs:
        merged = {**base_config, **model_dict}
        expanded.append(_ensure_config_id(merged))

    return expanded


def _ensure_config_id(config: dict[str, Any]) -> dict[str, Any]:
    """Ensure config has a config_id field, generating one if needed.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration dictionary with config_id field
    """
    if "config_id" not in config:
        config["config_id"] = generate_config_id(config)
    return config


def normalize_config(config: dict[str, Any] | BaseModel) -> dict[str, Any]:
    """Normalize config to dictionary form.

    Handles both dict and Pydantic BaseModel configs, converting models to dicts
    and ensuring config_id is present.

    Args:
        config: Configuration as dict or Pydantic model

    Returns:
        Normalized configuration dictionary with config_id
    """
    if isinstance(config, dict):
        config_dict = config
    elif isinstance(config, BaseModel):
        config_dict = config.model_dump()
    else:
        raise TypeError(f"Config must be dict or Pydantic BaseModel, got {type(config).__name__}")

    return _ensure_config_id(config_dict)


def merge_configs(
    base_configs: list[dict[str, Any]],
    override_configs: list[dict[str, Any]],
    strategy: str = "extend",
) -> list[dict[str, Any]]:
    """Merge two sets of configurations with specified strategy.

    Args:
        base_configs: Base configuration set
        override_configs: Override/extension configuration set
        strategy: Merging strategy - 'extend' (concatenate) or 'override' (replace matching)

    Returns:
        Merged configuration list

    Raises:
        ValueError: If strategy is not recognized
    """
    if strategy == "extend":
        # Simply concatenate, ensuring all have config_ids
        return [_ensure_config_id(c) for c in base_configs] + [
            _ensure_config_id(c) for c in override_configs
        ]
    elif strategy == "override":
        # Build lookup by config_id, with overrides taking precedence
        merged_dict: dict[str, dict[str, Any]] = {}

        for config in base_configs:
            config = _ensure_config_id(config)
            merged_dict[config["config_id"]] = config

        for config in override_configs:
            config = _ensure_config_id(config)
            merged_dict[config["config_id"]] = config

        return list(merged_dict.values())
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}. Use 'extend' or 'override'.")


__all__ = [
    "generate_config_id",
    "load_configs_from_yaml",
    "expand_configs_from_model",
    "normalize_config",
    "merge_configs",
]
