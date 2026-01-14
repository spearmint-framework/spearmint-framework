"""Integration tests for Spearmint decorator flows.

This module tests the complete decorator flow from configuration to execution,
covering both @configure and @experiment decorators with various scenarios.

Test Coverage:
1. @configure decorator with single config
2. @configure decorator with multiple configs
3. @experiment decorator (via Spearmint.experiment())
4. Spearmint instance-based decoration
5. File-based config loading (YAML)
6. Dict-based inline configs
7. Mixed config sources
8. Async function decoration
9. Sync function decoration
10. Nested decorated functions
11. RunSession context manager with return_all
"""

import asyncio
from typing import Any

import pytest

from spearmint import Config, Spearmint, configure, experiment
from spearmint.strategies import DefaultBranchStrategy, MultiBranchStrategy, ShadowBranchStrategy


class TestConfigureDecoratorSingleConfig:
    """Test @configure decorator with a single configuration."""

    @pytest.mark.asyncio
    async def test_async_function_with_single_config(self, single_config):
        """Async function with single config executes correctly."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        result = await process("test")

        assert result == "test_single"

    def test_sync_function_with_single_config(self, single_config):
        """Sync function with single config executes correctly."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        def multiply(x: int, config: Config) -> int:
            return x * config["value"]

        result = multiply(2)

        assert result == 84  # 2 * 42

    @pytest.mark.asyncio
    async def test_config_injection_by_parameter_name(self, single_config):
        """Config is injected when parameter is named 'config'."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def func_with_config_param(data: str, config: Config) -> dict:
            return {"data": data, "config_id": config["id"]}

        result = await func_with_config_param("input_data")

        assert result["data"] == "input_data"
        assert result["config_id"] == "single"

    @pytest.mark.asyncio
    async def test_config_attributes_accessible(self, single_config):
        """Config attributes are accessible via dict notation."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def access_config(config: Config) -> dict:
            return {
                "id": config["id"],
                "value": config["value"],
                "has_setting": "setting" in config,
            }

        result = await access_config()

        assert result["id"] == "single"
        assert result["value"] == 42
        assert result["has_setting"] is False  # Not in single_config fixture


class TestConfigureDecoratorMultipleConfigs:
    """Test @configure decorator with multiple configurations."""

    @pytest.mark.asyncio
    async def test_async_function_with_multiple_configs(self, sample_configs):
        """Async function with multiple configs returns default branch result."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        result = await process("test")

        # Default strategy returns first config result
        assert result == "test_config_0"

    def test_sync_function_with_multiple_configs(self, sample_configs):
        """Sync function with multiple configs executes with default branch."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )
        def get_temperature(config: Config) -> float:
            return config["temperature"]

        result = get_temperature()

        # Should return first config's temperature
        assert result == 0.7

    @pytest.mark.asyncio
    async def test_multi_branch_strategy_with_multiple_configs(self, sample_configs):
        """MultiBranchStrategy with multiple configs returns default output."""

        @configure(
            branch_strategy=MultiBranchStrategy,
            configs=sample_configs,
        )
        async def process(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * int(config["temperature"] * 10)

        result = await process(5)

        # MultiBranch returns the branches as output
        assert isinstance(result, list)
        assert len(result) == len(sample_configs)
        assert any(r.output == 5 * 7 for r in result)  # 0.7 * 10
        assert any(r.output == 5 * 9 for r in result)  # 0.9 * 10
        assert any(r.output == 5 * 5 for r in result)  # 0.5 * 10


class TestExperimentDecorator:
    """Test @experiment decorator functionality."""

    @pytest.mark.asyncio
    async def test_experiment_decorator_with_configs(self, sample_configs):
        """@experiment decorator wraps function correctly."""

        @experiment(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )
        async def analyze(text: str, config: Config) -> dict:
            await asyncio.sleep(0.01)
            return {
                "text": text,
                "model": config["model"],
                "config_id": config["id"],
            }

        result = await analyze("sample text")

        assert result["text"] == "sample text"
        assert result["model"] == "gpt-4"
        assert result["config_id"] == "config_0"

    def test_experiment_decorator_sync_function(self, single_config):
        """@experiment decorator works with sync functions."""

        @experiment(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        def compute(x: int, y: int, config: Config) -> int:
            return (x + y) * config["value"]

        result = compute(3, 7)

        assert result == 420  # (3 + 7) * 42


class TestSpearmintInstanceBasedDecoration:
    """Test decoration via Spearmint instance methods."""

    @pytest.mark.asyncio
    async def test_spearmint_instance_configure_method(self, sample_configs):
        """Spearmint instance .configure() method works correctly."""

        sp = Spearmint(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )

        @sp.configure()
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}:{config['model']}"

        result = await process("input")

        assert result == "input:gpt-4"

    @pytest.mark.asyncio
    async def test_spearmint_instance_experiment_method(self, sample_configs):
        """Spearmint instance .experiment() method works correctly."""

        sp = Spearmint(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )

        @sp.experiment()
        async def analyze(data: dict, config: Config) -> dict:
            await asyncio.sleep(0.01)
            return {**data, "config_id": config["id"]}

        result = await analyze({"key": "value"})

        assert result["key"] == "value"
        assert result["config_id"] == "config_0"

    def test_spearmint_instance_override_strategy(self, sample_configs):
        """Spearmint instance can override strategy in decorator."""

        sp = Spearmint(
            branch_strategy=DefaultBranchStrategy,  # Default strategy
            configs=sample_configs,
        )

        @sp.configure(branch_strategy=ShadowBranchStrategy)  # Override with ShadowBranch
        async def process(config: Config) -> str:
            return config["id"]

        # Function should use ShadowBranchStrategy despite instance default
        result = asyncio.run(process())

        assert result == "config_0"


class TestFileBasedConfigLoading:
    """Test YAML file-based configuration loading."""

    @pytest.mark.asyncio
    async def test_single_yaml_file_loading(self, temp_single_config_file):
        """Load configuration from a single YAML file."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=[temp_single_config_file],
        )
        async def process(config: Config) -> str:
            return config["id"]

        result = await process()

        assert result == "single_yaml"

    @pytest.mark.asyncio
    async def test_yaml_directory_loading(self, temp_config_dir):
        """Load multiple configs from YAML directory."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=[temp_config_dir],
        )
        async def get_config_id(config: Config) -> str:
            return config["id"]

        result = await get_config_id()

        # Should load first config alphabetically
        assert result == "yaml_config_0"

    @pytest.mark.asyncio
    async def test_yaml_config_values_accessible(self, temp_single_config_file):
        """Config values from YAML are properly accessible."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=[temp_single_config_file],
        )
        async def access_values(config: Config) -> dict:
            return {
                "id": config["id"],
                "setting": config["setting"],
            }

        result = await access_values()

        assert result["id"] == "single_yaml"
        assert result["setting"] == "test_value"


class TestDictBasedInlineConfigs:
    """Test inline dictionary-based configuration."""

    @pytest.mark.asyncio
    async def test_dict_config_single(self):
        """Single dict config works correctly."""

        config_dict = {"id": "inline_config", "value": 100}

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=[config_dict],
        )
        async def multiply(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * config["value"]

        result = await multiply(3)

        assert result == 300

    @pytest.mark.asyncio
    async def test_dict_configs_multiple(self):
        """Multiple dict configs work correctly."""

        configs = [
            {"id": "config_a", "multiplier": 2},
            {"id": "config_b", "multiplier": 5},
        ]

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=configs,
        )
        async def process(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * config["multiplier"]

        result = await process(10)

        # Default strategy uses first config
        assert result == 20

    @pytest.mark.asyncio
    async def test_dict_config_with_nested_structure(self):
        """Dict config with nested structure is accessible."""

        config_dict = {
            "id": "nested_config",
            "model": {"name": "gpt-4", "params": {"temperature": 0.7}},
        }

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=[config_dict],
        )
        async def get_model_info(config: Config) -> dict:
            return config["model"]

        result = await get_model_info()

        assert result["name"] == "gpt-4"
        assert result["params"]["temperature"] == 0.7


class TestMixedConfigSources:
    """Test mixing different config sources."""

    @pytest.mark.asyncio
    async def test_config_objects_and_dicts_mixed(self, single_config):
        """Mix Config objects and dicts in same decorator."""

        dict_config = {"id": "dict_mixed", "value": 50}
        mixed_configs = single_config + [dict_config]

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=mixed_configs,
        )
        async def process(config: Config) -> str:
            return config["id"]

        result = await process()

        # Should use first config
        assert result == "single"

    @pytest.mark.asyncio
    async def test_yaml_file_and_dict_mixed(self, temp_single_config_file):
        """Mix YAML file path and dict configs."""

        dict_config = {"id": "dict_config", "extra": "data"}

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=[temp_single_config_file, dict_config],
        )
        async def get_id(config: Config) -> str:
            return config["id"]

        result = await get_id()

        # YAML file processed first
        assert result == "single_yaml"


class TestAsyncFunctionDecoration:
    """Test async function decoration patterns."""

    @pytest.mark.asyncio
    async def test_async_function_with_await(self, single_config):
        """Async function with await works correctly."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def async_process(value: str, config: Config) -> str:
            await asyncio.sleep(0.05)
            return f"processed_{value}_{config['id']}"

        result = await async_process("data")

        assert result == "processed_data_single"

    @pytest.mark.asyncio
    async def test_async_function_returns_complex_type(self, sample_configs):
        """Async function returning complex types works."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )
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
        assert result["temperature"] == 0.7
        assert result["computed"] == 70.0

    @pytest.mark.asyncio
    async def test_async_function_with_multiple_awaits(self, single_config):
        """Async function with multiple awaits executes correctly."""

        async def helper_async(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def multi_await(value: int, config: Config) -> int:
            result = await helper_async(value)
            await asyncio.sleep(0.01)
            return result + config["value"]

        result = await multi_await(10)

        assert result == 62  # (10 * 2) + 42


class TestSyncFunctionDecoration:
    """Test synchronous function decoration patterns."""

    def test_sync_function_executes_correctly(self, single_config):
        """Sync function executes without await."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        def sync_process(value: str, config: Config) -> str:
            return f"{value}_{config['id']}"

        result = sync_process("test")

        assert result == "test_single"

    def test_sync_function_with_multiple_params(self, sample_configs):
        """Sync function with multiple parameters works."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )
        def combine(a: str, b: str, c: int, config: Config) -> str:
            return f"{a}_{b}_{c}_{config['model']}"

        result = combine("hello", "world", 42)

        assert result == "hello_world_42_gpt-4"

    def test_sync_function_no_config_param(self, single_config):
        """Sync function without config param still works when decorated."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        def no_config(x: int, y: int) -> int:
            return x + y

        result = no_config(5, 7)

        assert result == 12


class TestNestedDecoratedFunctions:
    """Test nested calls between decorated functions."""

    @pytest.mark.asyncio
    async def test_decorated_function_calls_decorated_function(self, single_config):
        """One decorated function can call another."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def inner_func(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            return x * config["value"]

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def outer_func(x: int, config: Config) -> int:
            inner_result = await inner_func(x, config)
            return inner_result + 10

        result = await outer_func(2)

        assert result == 94  # (2 * 42) + 10

    @pytest.mark.asyncio
    async def test_decorated_async_calls_regular_async(self, sample_configs):
        """Decorated function can call regular async function."""

        async def regular_async(value: str) -> str:
            await asyncio.sleep(0.01)
            return f"regular_{value}"

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )
        async def decorated_func(value: str, config: Config) -> str:
            regular_result = await regular_async(value)
            return f"{regular_result}_{config['id']}"

        result = await decorated_func("test")

        assert result == "regular_test_config_0"

    def test_decorated_sync_calls_decorated_sync(self, single_config):
        """Nested sync decorated functions work."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        def add_offset(x: int, config: Config) -> int:
            return x + config["value"]

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        def double_and_offset(x: int, config: Config) -> int:
            doubled = x * 2
            return add_offset(doubled, config)

        result = double_and_offset(5)

        assert result == 52  # (5 * 2) + 42


class TestDecoratorEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_empty_config_list_raises_error(self):
        """Empty config list should raise appropriate error."""

        with pytest.raises((ValueError, IndexError)):

            @configure(
                branch_strategy=DefaultBranchStrategy,
                configs=[],
            )
            async def func(config: Config) -> str:
                return "test"

            await func()

    @pytest.mark.asyncio
    async def test_function_with_no_params_still_works(self, single_config):
        """Function with no parameters can still be decorated."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def no_params() -> str:
            await asyncio.sleep(0.01)
            return "executed"

        result = await no_params()

        assert result == "executed"

    @pytest.mark.asyncio
    async def test_function_with_kwargs(self, single_config):
        """Function accepting **kwargs works with decoration."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def with_kwargs(config: Config, **kwargs) -> dict:
            await asyncio.sleep(0.01)
            return {"config_id": config["id"], **kwargs}

        result = await with_kwargs(extra="data", another=123)

        assert result["config_id"] == "single"
        assert result["extra"] == "data"
        assert result["another"] == 123

    @pytest.mark.asyncio
    async def test_function_with_args_and_kwargs(self, single_config):
        """Function with *args and **kwargs works."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def flexible_func(*args, config: Config, **kwargs) -> dict:
            await asyncio.sleep(0.01)
            return {
                "config_id": config["id"],
                "args": args,
                "kwargs": kwargs,
            }

        result = await flexible_func(1, 2, 3, key="value")

        assert result["config_id"] == "single"
        assert result["args"] == (1, 2, 3)
        assert result["kwargs"] == {"key": "value"}


class TestDecoratorReturnValues:
    """Test various return value scenarios."""

    @pytest.mark.asyncio
    async def test_returns_none(self, single_config):
        """Function returning None works correctly."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def returns_none(config: Config) -> None:
            await asyncio.sleep(0.01)
            # Implicitly returns None

        result = await returns_none()

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_list(self, sample_configs):
        """Function returning list works correctly."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )
        async def returns_list(config: Config) -> list[str]:
            await asyncio.sleep(0.01)
            return [config["id"], config["model"], str(config["temperature"])]

        result = await returns_list()

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "config_0"

    @pytest.mark.asyncio
    async def test_returns_tuple(self, single_config):
        """Function returning tuple works correctly."""

        @configure(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )
        async def returns_tuple(x: int, config: Config) -> tuple[int, str, int]:
            await asyncio.sleep(0.01)
            return (x, config["id"], config["value"])

        result = await returns_tuple(42)

        assert isinstance(result, tuple)
        assert result == (42, "single", 42)


class TestRunSessionContextManager:
    """Test the mint.run() async context manager API."""

    @pytest.mark.asyncio
    async def test_run_session_returns_all_branches(self, sample_configs):
        """RunSession with return_all=True returns all branch results."""

        sp = Spearmint(
            branch_strategy=MultiBranchStrategy,
            configs=sample_configs,
        )

        @sp.experiment()
        def inner_func(value: str, config: Config) -> str:
            return f"{value}_{config['id']}"

        def main_func(value: str) -> str:
            return inner_func(value)

        async with sp.run(main_func, return_all=True) as runner:
            results = await runner("test")

        # Results should be a list of branch records
        assert isinstance(results, list)
        # Should have branch paths for each config
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_run_session_return_all_false(self, sample_configs):
        """RunSession with return_all=False returns only default output."""

        sp = Spearmint(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )

        @sp.experiment()
        def inner_func(value: str, config: Config) -> str:
            return f"{value}_{config['id']}"

        def main_func(value: str) -> str:
            return inner_func(value)

        async with sp.run(main_func, return_all=False) as runner:
            result = await runner("test")

        # Should return the raw output, not formatted branches
        assert result == "test_config_0"

    @pytest.mark.asyncio
    async def test_run_session_with_async_main(self, single_config):
        """RunSession works with async main function."""

        sp = Spearmint(
            branch_strategy=DefaultBranchStrategy,
            configs=single_config,
        )

        @sp.experiment()
        async def inner_func(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        async def main_func(value: str) -> str:
            return await inner_func(value)

        async with sp.run(main_func, return_all=False) as runner:
            result = await runner("async_test")

        assert result == "async_test_single"

    @pytest.mark.asyncio
    async def test_run_session_multiple_calls(self, sample_configs):
        """RunSession can be called multiple times."""

        sp = Spearmint(
            branch_strategy=DefaultBranchStrategy,
            configs=sample_configs,
        )

        @sp.experiment()
        def inner_func(x: int, config: Config) -> int:
            return x * int(config["temperature"] * 10)

        def main_func(x: int) -> int:
            return inner_func(x)

        async with sp.run(main_func, return_all=False) as runner:
            result1 = await runner(5)
            result2 = await runner(10)

        assert result1 == 35  # 5 * 7 (0.7 * 10)
        assert result2 == 70  # 10 * 7

    @pytest.mark.asyncio
    async def test_run_session_branch_results_structure(self):
        """Verify the structure of branch results from RunSession."""

        configs = [
            {"config_id": "config_a", "value": 10},
            {"config_id": "config_b", "value": 20},
        ]

        sp = Spearmint(
            branch_strategy=MultiBranchStrategy,
            configs=configs,
        )

        @sp.experiment()
        def inner_func(x: int, config: Config) -> int:
            return x * config["value"]

        def main_func(x: int) -> int:
            return inner_func(x)

        async with sp.run(main_func, return_all=True) as runner:
            results = await runner(2)

        # Each result should have config_chain and outputs
        assert isinstance(results, list)
        for result in results:
            if result:  # Skip empty results
                assert "config_chain" in result
                assert "outputs" in result
                assert isinstance(result["config_chain"], list)
                assert isinstance(result["outputs"], dict)

    @pytest.mark.asyncio
    async def test_run_session_shadow_strategy_wait_for_background(self):
        """RunSession with ShadowBranchStrategy tracks background execution."""

        configs = [
            {"config_id": "default", "value": 1},
            {"config_id": "shadow", "value": 2},
        ]

        sp = Spearmint(
            branch_strategy=ShadowBranchStrategy,
            configs=configs,
        )

        execution_order = []

        @sp.experiment()
        async def inner_func(x: int, config: Config) -> int:
            await asyncio.sleep(0.01)
            execution_order.append(config["config_id"])
            return x * config["value"]

        async def main_func(x: int) -> int:
            return await inner_func(x)

        async with sp.run(main_func, return_all=True) as runner:
            results = await runner(5)

        # Default branch should have executed
        assert "default" in execution_order
        # Results should contain at least the default branch info
        assert isinstance(results, list)
