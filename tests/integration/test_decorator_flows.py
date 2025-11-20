
"""Integration tests for Spearmint experiment decorator flows."""

import asyncio
from pathlib import Path
from typing import Any

import pytest

from spearmint import Config, Spearmint, experiment
from spearmint.core.trace import trace_manager
from spearmint.strategies import DefaultBranchStrategy, MultiBranchStrategy, ShadowBranchStrategy


class TestExperimentDecoratorSingleConfig:
    """Exercise the experiment decorator with a single configuration."""

    @pytest.mark.asyncio
    async def test_async_function_with_single_config(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        assert await process("test") == "test_single"

    def test_sync_function_with_single_config(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        def multiply(x: int, config: Config) -> int:
            return x * config["value"]

        assert multiply(2) == 84

    @pytest.mark.asyncio
    async def test_config_injection_by_parameter_name(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def func_with_config_param(data: str, config: Config) -> dict:
            return {"data": data, "config_id": config["id"]}

        result = await func_with_config_param("input_data")
        assert result == {"data": "input_data", "config_id": "single"}

    @pytest.mark.asyncio
    async def test_config_attributes_accessible(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def access_config(config: Config) -> dict:
            return {
                "id": config["id"],
                "value": config["value"],
                "has_setting": "setting" in config,
            }

        result = await access_config()
        assert result == {"id": "single", "value": 42, "has_setting": False}


class TestExperimentDecoratorMultipleConfigs:
    """Ensure experiment decorator works with multiple configurations."""

    @pytest.mark.asyncio
    async def test_async_function_with_multiple_configs(self, sample_configs):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=sample_configs)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        assert await process("test") == "test_config_0"

    def test_sync_function_with_multiple_configs(self, sample_configs):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=sample_configs)
        def get_temperature(config: Config) -> float:
            return config["temperature"]

        assert get_temperature() == 0.7

    @pytest.mark.asyncio
    async def test_multi_branch_strategy_with_multiple_configs(self, sample_configs):
        @experiment(branch_strategy=MultiBranchStrategy, configs=sample_configs)
        async def process(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * int(config["temperature"] * 10)

        result = await process(5)
        assert isinstance(result, list)
        assert len(result) == len(sample_configs)
        assert {r.output for r in result} >= {5 * 7, 5 * 9, 5 * 5}


class TestSpearmintInstanceDecoration:
    """Verify Spearmint instance helper uses the experiment decorator pipeline."""

    @pytest.mark.asyncio
    async def test_spearmint_instance_method(self, sample_configs):
        mint = Spearmint(branch_strategy=DefaultBranchStrategy, configs=sample_configs)

        @mint.experiment()
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}:{config['model']}"

        assert await process("input") == "input:gpt-4"

    def test_spearmint_instance_override_strategy(self, sample_configs):
        mint = Spearmint(branch_strategy=DefaultBranchStrategy, configs=sample_configs)

        @mint.experiment(branch_strategy=ShadowBranchStrategy)
        async def process(config: Config) -> str:
            return config["id"]

        assert asyncio.run(process()) == "config_0"


class TestConfigSources:
    """Exercise different configuration sources (YAML, dicts, mixes)."""

    @pytest.mark.asyncio
    async def test_single_yaml_file_loading(self, temp_single_config_file):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=[temp_single_config_file])
        async def process(config: Config) -> str:
            return config["id"]

        assert await process() == "single_yaml"

    @pytest.mark.asyncio
    async def test_yaml_directory_loading(self, temp_config_dir):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=[temp_config_dir])
        async def get_config_id(config: Config) -> str:
            return config["id"]

        assert await get_config_id() == "yaml_config_0"

    @pytest.mark.asyncio
    async def test_dict_config_single(self):
        config_dict = {"id": "inline_config", "value": 100}

        @experiment(branch_strategy=DefaultBranchStrategy, configs=[config_dict])
        async def multiply(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * config["value"]

        assert await multiply(3) == 300

    @pytest.mark.asyncio
    async def test_dict_configs_multiple(self):
        configs: list[dict[str, Any] | Config | str | Path] = [
            {"id": "config_a", "multiplier": 2},
            {"id": "config_b", "multiplier": 5},
        ]

        @experiment(branch_strategy=DefaultBranchStrategy, configs=configs)
        async def process(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * config["multiplier"]

        assert await process(10) == 20

    @pytest.mark.asyncio
    async def test_mixed_config_sources(self, single_config, temp_single_config_file):
        configs = single_config + [temp_single_config_file]

        @experiment(branch_strategy=DefaultBranchStrategy, configs=configs)
        async def choose(config: Config) -> str:
            return config["id"]

        assert await choose() == "single"


class TestFunctionPatterns:
    """Cover assorted async/sync patterns and nested calls."""

    @pytest.mark.asyncio
    async def test_async_function_returns_complex_type(self, sample_configs):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=sample_configs)
        async def get_config_dict(config: Config) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {
                "config_id": config["id"],
                "temperature": config["temperature"],
                "model": config["model"],
                "computed": config["temperature"] * 100,
            }

        result = await get_config_dict()
        assert result["config_id"] == "config_0"

    @pytest.mark.asyncio
    async def test_nested_decorated_functions(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def inner_func(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * config["value"]

        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def outer_func(x: int, config: Config) -> int:
            inner_result = await inner_func(x, config)
            return inner_result + 10

        assert await outer_func(2) == 94

    def test_sync_function_no_config_param(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        def no_config(x: int, y: int) -> int:
            return x + y

        assert no_config(5, 7) == 12


class TestShadowBranchStrategy:
    """Validate shadow strategy behavior with nested experiment calls."""

    @pytest.mark.asyncio
    async def test_shadow_strategy_nested_functions_unique_results(self, sample_configs):
        class _Collector:
            def __init__(self) -> None:
                self.finished: list[Any] = []

            def on_start(self, trace) -> None:  # pragma: no cover - not used in assertions
                pass

            def on_end(self, trace, error) -> None:
                self.finished.append(trace)

        collector = _Collector()
        trace_manager.register_exporter(collector)

        try:
            @experiment(branch_strategy=ShadowBranchStrategy, configs=sample_configs)
            async def outer(seed: int, *, config: Config) -> str:
                @experiment(branch_strategy=ShadowBranchStrategy, configs=sample_configs)
                async def inner_local(value: int, *, config: Config) -> str:
                    await asyncio.sleep(0.005)
                    return f"inner-{config['id']}-{value}"

                inner_value = await inner_local(seed + int(config["id"][-1]))
                unique_result = f"{config['id']}::{inner_value}"
                return unique_result

            default_result = await outer(7)
            expected_results = [
                "config_0::inner-config_0-7",
                "config_0::inner-config_1-7",
                "config_0::inner-config_2-7",
                "config_1::inner-config_0-8",
                "config_1::inner-config_1-8",
                "config_1::inner-config_2-8",
                "config_2::inner-config_0-9",
                "config_2::inner-config_1-9",
                "config_2::inner-config_2-9",
            ]
            outer_traces: list[Any] = []
            for _ in range(20):
                outer_traces = [
                    trace
                    for trace in collector.finished
                    if trace.name == "branch" and trace.data.get("func") == "outer"
                ]
                if len(outer_traces) == len(expected_results):
                    break
                await asyncio.sleep(0.1)
        finally:
            trace_manager.unregister_exporter(collector)

        trace_results = [trace.data.get("return_value") for trace in outer_traces]
        for r in trace_results:
            print(r)
        assert len(outer_traces) == len(expected_results)
        assert set(trace_results) == set(expected_results)



class TestEdgeCases:
    """Edge cases and return-shape scenarios for experiment decorator."""

    @pytest.mark.asyncio
    async def test_empty_config_list_raises_error(self):
        with pytest.raises((ValueError, IndexError)):

            @experiment(branch_strategy=DefaultBranchStrategy, configs=[])
            async def func(config: Config) -> str:
                return "test"

            await func()

    @pytest.mark.asyncio
    async def test_function_with_kwargs(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def with_kwargs(config: Config, **kwargs) -> dict:
            await asyncio.sleep(0.01)
            return {"config_id": config["id"], **kwargs}

        result = await with_kwargs(extra="data", another=123)
        assert result == {"config_id": "single", "extra": "data", "another": 123}

    @pytest.mark.asyncio
    async def test_function_with_args_and_kwargs(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def flexible_func(*args, config: Config, **kwargs) -> dict:
            await asyncio.sleep(0.01)
            return {
                "config_id": config["id"],
                "args": args,
                "kwargs": kwargs,
            }

        result = await flexible_func(1, 2, 3, key="value")
        assert result["args"] == (1, 2, 3)

    @pytest.mark.asyncio
    async def test_returns_none(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def returns_none(config: Config) -> None:
            await asyncio.sleep(0.01)

        assert await returns_none() is None

    @pytest.mark.asyncio
    async def test_returns_list(self, sample_configs):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=sample_configs)
        async def returns_list(config: Config) -> list[str]:
            await asyncio.sleep(0.01)
            return [config["id"], config["model"], str(config["temperature"])]

        result = await returns_list()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_returns_tuple(self, single_config):
        @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
        async def returns_tuple(x: int, config: Config) -> tuple[int, str, int]:
            await asyncio.sleep(0.01)
            return (x, config["id"], config["value"])

        assert await returns_tuple(42) == (42, "single", 42)


class TestTraceInstrumentation:
    """Verify traces capture invocation metadata."""

    class _Collector:
        def __init__(self) -> None:
            self.started: list[Any] = []

        def on_start(self, trace) -> None:
            self.started.append(trace)

        def on_end(self, trace, error) -> None:  # pragma: no cover - not used in assertions
            pass

    @pytest.mark.asyncio
    async def test_trace_records_arguments(self, single_config):
        collector = self._Collector()
        trace_manager.register_exporter(collector)

        try:
            @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
            async def echo(value: str, config: Config) -> str:
                await asyncio.sleep(0.01)
                return f"{value}:{config['id']}"

            result = await echo("trace-value")
        finally:
            trace_manager.unregister_exporter(collector)

        assert result == "trace-value:single"
        branch_trace = next(trace for trace in reversed(collector.started) if trace.name == "branch")

        recorded_args = branch_trace.data.get("args", ())
        assert recorded_args and recorded_args[0] == "trace-value"
        assert "kwargs" in branch_trace.data

    @pytest.mark.asyncio
    async def test_nested_traces_capture_hierarchy(self, single_config):
        collector = self._Collector()
        trace_manager.register_exporter(collector)

        try:
            @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
            async def inner(x: int, config: Config) -> int:
                await asyncio.sleep(0.005)
                return x + config["value"]

            @experiment(branch_strategy=DefaultBranchStrategy, configs=single_config)
            async def outer(x: int, config: Config) -> int:
                inner_result = await inner(x, config)
                return inner_result - config["value"]

            result = await outer(10)
        finally:
            trace_manager.unregister_exporter(collector)

        assert result == 10

        branch_traces = [trace for trace in collector.started if trace.name == "branch"]
        assert len(branch_traces) >= 2
        outer_trace, inner_trace = branch_traces[-2], branch_traces[-1]

        assert inner_trace.parent is outer_trace
        assert inner_trace in outer_trace.children
        assert inner_trace.data.get("func") == "inner"
        assert outer_trace.data.get("func") == "outer"
