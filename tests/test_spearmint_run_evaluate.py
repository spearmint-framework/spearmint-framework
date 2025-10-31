"""Tests for Spearmint.run and Spearmint.evaluate methods."""

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

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

        output = mint.run(my_func, dataset, skip_eval=True)

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

        output = mint.run(my_func, dataset, skip_eval=True)

        assert len(output) == 2
        assert results == [15, 20]

    def test_run_adds_id_to_dataset_lines(self):
        """Test that run adds _id to each line if not present."""
        mint = Spearmint(configs=[{"value": 10}])

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [
            {"x": 5, "expected": 15},
            {"x": 10, "expected": 20},
        ]

        output = mint.run(my_func, dataset, skip_eval=True)

        assert "_id" in output[0]
        assert "_id" in output[1]
        assert isinstance(output[0]["_id"], UUID)
        assert isinstance(output[1]["_id"], UUID)

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

        output = mint.run(my_func, dataset, skip_eval=True)

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

        output = mint.run(my_func, dataset_file, skip_eval=True)

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

        output = mint.run(my_func, dataset, skip_eval=True)

        assert len(output) == 1
        assert output[0]["x"] == 5
        assert output[0]["y"] == 100  # Extra fields preserved

    def test_run_calls_evaluate_by_default(self):
        """Test that run calls evaluate when skip_eval is False."""
        mint = Spearmint(configs=[{"value": 10}])

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15}]

        with patch.object(mint, "evaluate", return_value=dataset) as mock_evaluate:
            mint.run(my_func, dataset, skip_eval=False)
            mock_evaluate.assert_called_once_with(dataset)

    def test_run_skips_evaluate_when_requested(self):
        """Test that run skips evaluate when skip_eval is True."""
        mint = Spearmint(configs=[{"value": 10}])

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15}]

        with patch.object(mint, "evaluate") as mock_evaluate:
            mint.run(my_func, dataset, skip_eval=True)
            mock_evaluate.assert_not_called()

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

        output = mint.run(my_func, dataset, skip_eval=True)

        assert len(output) == 3
        # Round robin should use different configs
        assert results == [15, 25, 35]


class TestSpearmintEvaluate:
    """Test Spearmint.evaluate method functionality."""

    def test_evaluate_with_single_evaluator(self) -> None:
        """Test evaluate with a single evaluator function."""
        mint = Spearmint(configs=[{"value": 10}])

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            """Simple accuracy evaluator."""
            return 1.0 if expected == 15 else 0.0

        @mint.experiment(evaluators=[accuracy_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        line_id = uuid4()
        config_id = mint.configs[0]["config_id"]
        dataset = [{"x": 5, "expected": 15, "_id": line_id}]

        # Mock mlflow.search_traces to return a trace with proper structure
        mock_trace = Mock()
        mock_trace.to_dict.return_value = {
            "info": {"request_id": "test-id"},
            "data": {"spans": [{"attributes": {"config_id": config_id, "line_id": str(line_id)}}]},
        }

        with patch("mlflow.search_traces", return_value=[mock_trace]):
            output = mint.evaluate(dataset)

        assert len(output) == 1
        assert "_evaluations" in output[0]
        assert "accuracy_eval" in output[0]["_evaluations"]

    def test_evaluate_with_multiple_evaluators(self) -> None:
        """Test evaluate with multiple evaluator functions."""
        mint = Spearmint(configs=[{"value": 10}])

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            return 1.0

        def precision_eval(expected: int, trace: dict[str, Any]) -> float:
            return 0.9

        @mint.experiment(evaluators=[accuracy_eval, precision_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        line_id = uuid4()
        config_id = mint.configs[0]["config_id"]
        dataset = [{"x": 5, "expected": 15, "_id": line_id}]

        mock_trace = create_mock_trace(config_id, line_id)

        with patch("mlflow.search_traces", return_value=[mock_trace]):
            output = mint.evaluate(dataset)

        assert "_evaluations" in output[0]
        assert "accuracy_eval" in output[0]["_evaluations"]
        assert "precision_eval" in output[0]["_evaluations"]
        assert output[0]["_evaluations"]["accuracy_eval"] == 1.0
        assert output[0]["_evaluations"]["precision_eval"] == 0.9

    def test_evaluate_with_multiple_configs(self) -> None:
        """Test evaluate with multiple configurations."""
        mint = Spearmint()
        mint.configs = [Config({"value": 10}), Config({"value": 20})]

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            return 1.0

        @mint.experiment(evaluators=[accuracy_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        line_id = uuid4()
        config_id1 = mint.configs[0]["config_id"]
        config_id2 = mint.configs[1]["config_id"]
        dataset = [{"x": 5, "expected": 15, "_id": line_id}]

        # Create mock traces for both configs
        mock_trace1 = create_mock_trace(config_id1, line_id)
        mock_trace2 = create_mock_trace(config_id2, line_id)

        with patch("mlflow.search_traces", return_value=[mock_trace1, mock_trace2]):
            # First create the experiment info
            mint._experiments["my_func"] = {
                "evaluators": [accuracy_eval],
                "config_ids": [cfg["config_id"] for cfg in mint.configs],
            }

            output = mint.evaluate(dataset)

        assert "_evaluations" in output[0]

    def test_evaluate_stores_results_in_experiment_info(self):
        """Test that evaluate stores results in experiment info."""
        mint = Spearmint(configs=[{"value": 10}])

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            return 0.95

        @mint.experiment(evaluators=[accuracy_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15, "_id": uuid4()}]
        line_id = dataset[0]["_id"]
        config_id = mint.configs[0]["config_id"]

        mock_trace = create_mock_trace(config_id, line_id)

        with patch("mlflow.search_traces", return_value=[mock_trace]):
            mint.evaluate(dataset)

        # Check that evaluations are stored in experiment info
        assert "my_func" in mint._experiments
        assert "evaluations" in mint._experiments["my_func"]
        assert len(mint._experiments["my_func"]["evaluations"]) > 0

    def test_evaluate_with_no_trace_found_raises_error(self):
        """Test that evaluate raises error when trace is not found."""
        mint = Spearmint(configs=[{"value": 10}])

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            return 1.0

        @mint.experiment(evaluators=[accuracy_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15, "_id": uuid4()}]

        # Mock search_traces to return empty list
        with patch("mlflow.search_traces", return_value=[]):
            with pytest.raises(ValueError, match="No trace found"):
                mint.evaluate(dataset)

    def test_evaluate_passes_trace_to_evaluator(self):
        """Test that evaluate passes the correct trace to evaluator."""
        mint = Spearmint(configs=[{"value": 10}])

        received_traces = []

        def trace_capturing_eval(expected: int, trace: dict[str, Any]) -> float:
            received_traces.append(trace)
            return 1.0

        @mint.experiment(evaluators=[trace_capturing_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15, "_id": uuid4()}]

        mock_trace = create_mock_trace(mint.configs[0]["config_id"], dataset[0]["_id"])
        expected_trace = dict(mock_trace.to_dict())

        with patch("mlflow.search_traces", return_value=[mock_trace]):
            mint.evaluate(dataset)

        assert len(received_traces) == 1
        assert received_traces[0] == expected_trace

    def test_evaluate_includes_config_id_in_results(self):
        """Test that evaluate includes config_id in evaluation results."""
        mint = Spearmint(configs=[{"value": 10}])

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            return 1.0

        @mint.experiment(evaluators=[accuracy_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15, "_id": uuid4()}]

        mock_trace = create_mock_trace(mint.configs[0]["config_id"], dataset[0]["_id"])

        with patch("mlflow.search_traces", return_value=[mock_trace]):
            output = mint.evaluate(dataset)

        assert "config_id" in output[0]["_evaluations"]

    def test_evaluate_with_no_evaluators(self):
        """Test evaluate when no evaluators are registered."""
        mint = Spearmint(configs=[{"value": 10}])

        @mint.experiment()
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15, "_id": uuid4()}]

        mock_trace = create_mock_trace(mint.configs[0]["config_id"], dataset[0]["_id"])

        with patch("mlflow.search_traces", return_value=[mock_trace]):
            output = mint.evaluate(dataset)

        # The experiment will have empty evaluators list
        assert len(output) == 1


class TestSpearmintIntegration:
    """Integration tests for run and evaluate together."""

    def test_run_and_evaluate_integration(self):
        """Test full integration of run and evaluate."""
        mint = Spearmint(configs=[{"value": 10}])

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            # Simple check based on expected value
            return 1.0 if expected == 15 else 0.0

        @mint.experiment(evaluators=[accuracy_eval])
        def my_func(x: int, config: Config) -> int:
            return x + config["value"]

        dataset = [
            {"x": 5, "expected": 15, "_id": uuid4()},
            {"x": 10, "expected": 20, "_id": uuid4()},
        ]

        # Mock mlflow traces
        mock_trace1 = create_mock_trace(mint.configs[0]["config_id"], dataset[0]["_id"])
        mock_trace2 = create_mock_trace(mint.configs[0]["config_id"], dataset[1]["_id"])

        with patch("mlflow.search_traces", return_value=[mock_trace1, mock_trace2]):
            output = mint.run(my_func, dataset, skip_eval=False)

        # Check that evaluation was performed
        assert len(output) == 2
        assert "_id" in output[0]
        assert "_evaluations" in output[0]
        assert "accuracy_eval" in output[0]["_evaluations"]

    def test_async_run_and_evaluate_integration(self) -> None:
        """Test full integration of run and evaluate with async function."""
        mint = Spearmint(configs=[{"value": 10}])

        def accuracy_eval(expected: int, trace: dict[str, Any]) -> float:
            return 1.0

        @mint.experiment(evaluators=[accuracy_eval])
        async def my_func(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)  # Simulate async work
            return x + config["value"]

        dataset = [{"x": 5, "expected": 15, "_id": uuid4()}]

        mock_trace = create_mock_trace(mint.configs[0]["config_id"], dataset[0]["_id"])

        with patch("mlflow.search_traces", return_value=[mock_trace]):
            output = mint.run(my_func, dataset, skip_eval=False)

        assert len(output) == 1
        assert "_evaluations" in output[0]
