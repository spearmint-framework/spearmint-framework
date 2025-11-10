"""Shared pytest fixtures for Spearmint integration tests."""

import time
from pathlib import Path
from typing import Any

import pytest

from spearmint import Config


@pytest.fixture
def sample_configs() -> list[Config]:
    """Standard test configs with different parameters."""
    return [
        Config({"id": "config_0", "temperature": 0.7, "model": "gpt-4"}),
        Config({"id": "config_1", "temperature": 0.9, "model": "gpt-4"}),
        Config({"id": "config_2", "temperature": 0.5, "model": "gpt-3.5-turbo"}),
    ]


@pytest.fixture
def single_config() -> list[Config]:
    """Single config for testing default behavior."""
    return [Config({"id": "single", "value": 42})]


@pytest.fixture
def config_dicts() -> list[dict[str, Any]]:
    """Raw config dictionaries for testing dict-based initialization."""
    return [
        {"id": "dict_0", "param_a": "value_a"},
        {"id": "dict_1", "param_a": "value_b"},
    ]


@pytest.fixture
def execution_tracker():
    """Track function execution order, timing, and config IDs."""
    
    class ExecutionTracker:
        def __init__(self):
            self.calls: list[tuple[str, float]] = []
            self.start_time = time.time()
        
        def record(self, config_id: str) -> None:
            """Record a function call with config ID and timestamp."""
            elapsed = time.time() - self.start_time
            self.calls.append((config_id, elapsed))
        
        def get_call_count(self) -> int:
            """Get total number of calls."""
            return len(self.calls)
        
        def get_config_ids(self) -> list[str]:
            """Get list of config IDs in execution order."""
            return [call[0] for call in self.calls]
        
        def get_timings(self) -> list[float]:
            """Get list of execution timings."""
            return [call[1] for call in self.calls]
        
        def reset(self) -> None:
            """Reset the tracker."""
            self.calls = []
            self.start_time = time.time()
    
    return ExecutionTracker()


@pytest.fixture
def temp_config_dir(tmp_path) -> Path:
    """Create a temporary directory with YAML config files."""
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    
    # Create multiple config files
    (config_dir / "config0.yaml").write_text(
        "id: yaml_config_0\n"
        "temperature: 0.7\n"
        "max_tokens: 100\n"
    )
    
    (config_dir / "config1.yaml").write_text(
        "id: yaml_config_1\n"
        "temperature: 0.9\n"
        "max_tokens: 150\n"
    )
    
    return config_dir


@pytest.fixture
def temp_single_config_file(tmp_path) -> Path:
    """Create a single YAML config file."""
    config_file = tmp_path / "single_config.yaml"
    config_file.write_text(
        "id: single_yaml\n"
        "setting: test_value\n"
    )
    return config_file
