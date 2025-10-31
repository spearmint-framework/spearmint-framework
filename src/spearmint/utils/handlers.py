import json
from pathlib import Path
from typing import Any

import yaml


def jsonl_handler(file_path: str | Path) -> list[dict[str, Any]]:
    """
    Handler for reading JSON Lines files.

    Args:
        file_path: Path to the JSON Lines file.

    Returns:
        A list of dictionaries representing the JSON Lines data.
    """

    with open(file_path, "r") as f:
        return [json.loads(line) for line in f]


def yaml_handler(file_path: str | Path) -> list[dict[str, Any]]:
    """
    Handler for reading YAML files.

    Args:
        file_path: Path to the YAML file.

    Returns:
        A dictionary representing the YAML data.
    """
    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"Configuration path does not exist: {file_path}")

    configs: list[dict[str, Any]] = []

    if path_obj.is_file():
        configs.append(_load_yaml_file(path_obj))
    elif path_obj.is_dir():
        # Load all YAML files in directory (recursively)
        for yaml_file in sorted(path_obj.rglob("*.yaml")) + sorted(
            path_obj.rglob("*.yml")
        ):
            configs.append(_load_yaml_file(yaml_file))

    return configs


def _load_yaml_file(file_path: Path) -> dict[str, Any]:
    with open(file_path, "r") as f:
        return yaml.safe_load(f)
