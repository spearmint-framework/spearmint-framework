"""Configuration management utilities."""

import hashlib
import json
from typing import Any

from pydantic import RootModel, model_validator


class Config(RootModel[dict[str, Any]]):
    """Configuration model for experiment parameters."""

    root: dict[str, Any]

    @model_validator(mode="after")
    def _add_config_id(self) -> "Config":
        """Add config_id to root dictionary after validation."""
        if "config_id" not in self.root:
            self.root["config_id"] = _generate_config_id(self.root)
        return self

    def __getitem__(self, key: str) -> Any:
        """Enable dict-like access: config['key']."""
        return self.root[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Enable dict-like assignment: config['key'] = value."""
        self.root[key] = value

    def __getattr__(self, key: str) -> Any:
        """Enable dot notation access: config.key."""
        try:
            return self.root[key]
        except KeyError as exc:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            ) from exc

    def __contains__(self, key: str) -> bool:
        """Enable 'key' in config checks."""
        return key in self.root


def _generate_config_id(config: dict[str, Any]) -> str:
    """Generate a unique config ID based on the config and index.

    Args:
        config: Configuration dictionary
    Returns:
        Unique configuration ID as a string
    """

    if "config_id" in config:
        return str(config["config_id"])

    # Otherwise, compute hash from normalized content
    # Sort keys for deterministic ordering
    # Exclude config_id from hash calculation to avoid circular dependency
    config_copy = {k: v for k, v in config.items() if k != "config_id"}
    normalized = json.dumps(config_copy, sort_keys=True, default=str)
    hash_obj = hashlib.sha256(normalized.encode("utf-8"))
    return hash_obj.hexdigest()[:16]  # Use first 16 chars for brevity
