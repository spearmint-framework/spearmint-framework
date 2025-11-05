"""Tests for Spearmint.run and Spearmint.evaluate methods."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

from spearmint import Spearmint
from spearmint.config import Config
from spearmint.strategies import RoundRobinStrategy


def create_mock_trace(config_id: str, line_id: Any) -> Mock:
    """Helper to create a properly structured mock trace."""
    mock_trace = Mock()
    mock_trace.to_dict.return_value = {
        "info": {"request_id": "test-id"},
        "data": {"spans": [{"attributes": {"config_id": config_id, "line_id": str(line_id)}}]},
    }
    return mock_trace


class TestSpearmintRun:
    """Test Spearmint.run method functionality."""

    def test_run_with_sync_function_and_dict_dataset(self):
        """Test run with synchronous function and dict dataset."""
        mint = Spearmint(configs=[{"value": 10}])

        results = []

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            result = x + config["value"]
            results.append(result)
            return result

        dataset = [
            {"x": 5, "expected": 15},
            {"x": 10, "expected": 20},
        ]

        output = mint.run(my_func, dataset)

        assert len(output) == 2
        assert results == [15, 20]
        assert output[0]["x"] == 5
        assert output[1]["x"] == 10

    def test_run_with_async_function_and_dict_dataset(self) -> None:
        """Test run with async function and dict dataset."""
        mint = Spearmint(configs=[{"value": 10}])

        results = []

        @mint.experiment()
        async def my_func(x: int, config: Config) -> int:
            result = x + config["value"]
            results.append(result)
            return result

        dataset = [
            {"x": 5, "expected": 15},
            {"x": 10, "expected": 20},
        ]

        output = mint.run(my_func, dataset)

        assert len(output) == 2
        assert results == [15, 20]

    def test_run_preserves_existing_id(self):
        """Test that run preserves existing _id values."""
        mint = Spearmint(configs=[{"value": 10}])

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        id1 = uuid4()
        id2 = uuid4()
        dataset = [
            {"x": 5, "expected": 15, "_id": id1},
            {"x": 10, "expected": 20, "_id": id2},
        ]

        output = mint.run(my_func, dataset)

        assert output[0]["_id"] == id1
        assert output[1]["_id"] == id2

    def test_run_with_path_dataset(self, tmp_path: Path):
        """Test run with dataset loaded from file path."""
        mint = Spearmint(configs=[{"value": 10}])

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        # Create a test dataset file
        dataset_file = tmp_path / "test_dataset.jsonl"
        dataset_file.write_text('{"x": 5, "expected": 15}\n{"x": 10, "expected": 20}\n')

        output = mint.run(my_func, dataset_file)

        assert len(output) == 2
        assert output[0]["x"] == 5
        assert output[1]["x"] == 10

    def test_run_with_partial_params(self):
        """Test run matches only available parameters."""
        mint = Spearmint(configs=[{"value": 10}])

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        # Dataset has extra fields that aren't in function signature
        dataset = [
            {"x": 5, "y": 100, "z": 200, "expected": 15},
        ]

        output = mint.run(my_func, dataset)

        assert len(output) == 1
        assert output[0]["x"] == 5
        assert output[0]["y"] == 100  # Extra fields preserved

    def test_run_with_multiple_configs_round_robin(self) -> None:
        """Test run with multiple configs using RoundRobinStrategy."""
        # Create Config objects explicitly
        mint = Spearmint()
        mint.configs = [Config({"value": 10}), Config({"value": 20}), Config({"value": 30})]

        results = []

        @mint.experiment(strategy=RoundRobinStrategy)
        def my_func(x: int, config: Config) -> int:
            result = x + config["value"]
            results.append(result)
            return result

        dataset = [
            {"x": 5, "expected": 15},
            {"x": 5, "expected": 25},
            {"x": 5, "expected": 35},
        ]

        output = mint.run(my_func, dataset)

        assert len(output) == 3
        # Round robin should use different configs
        assert results == [15, 25, 35]
