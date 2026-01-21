import asyncio
from typing import Annotated, Any

import pytest

from spearmint import Spearmint, Config, experiment
from spearmint.configuration import Bind
from spearmint.spearmint import current_experiment_case, experiment_fn_registry


class TestSpearmint:
    """Test @configure decorator with a single configuration."""

    @pytest.mark.asyncio
    async def test_basic_experiment(self):
        single_config = [{"id": "single"}]

        @experiment(configs=single_config)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        async with Spearmint.run(process) as runner:
            results = await runner("test")

        assert results.main_result.result == "test_single"
        assert results.variant_results == []

    @pytest.mark.asyncio
    async def test_experiment_default_binding(self):
        bound_config = [
            {
                "bound": {
                    "config": {
                        "id": "my_bound_config"
                    }
                }
            }
        ]

        @experiment(configs=bound_config)
        async def process(value: str, config: Annotated[Config, Bind("bound.config")]) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"
        
        # Test direct call with DI
        result = await process("test")
        assert result == "test_my_bound_config"

        # Test via Spearmint.run
        async with Spearmint.run(process) as runner:
            results = await runner("test")

        assert results.main_result.result == "test_my_bound_config"
        assert results.variant_results == []

    @pytest.mark.asyncio
    async def test_experiment_no_configs(self):
        @experiment(configs=[])
        async def process(value: str) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_no_config"
        
        result = await process("test")
        assert result == "test_no_config"

        async with Spearmint.run(process) as runner:
            results = await runner("test")

        assert results.main_result.result == "test_no_config"
        assert results.variant_results == []

    @pytest.mark.asyncio
    async def test_nested_experiments_multiple_configs(self):
        inner_configs = [
            {"id": "inner_a"},
            {"id": "inner_b"},
        ]
        outer_configs = [
            {"id": "outer_a"},
            {"id": "outer_b"},
        ]

        @experiment(configs=inner_configs)
        async def inner(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        @experiment(configs=outer_configs)
        async def outer(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            inner_result = await inner(value)
            return f"{config['id']}|{inner_result}"

        async with Spearmint.run(outer, await_background_cases=True) as runner:
            results = await runner("test")

        assert results.main_result.result == "outer_a|test_inner_a"
        assert len(results.variant_results) == 3

        variant_values = {r.result for r in results.variant_results}
        assert variant_values == {
            "outer_a|test_inner_b",
            "outer_b|test_inner_a",
            "outer_b|test_inner_b",
        }

    @pytest.mark.asyncio
    async def test_nested_experiment_outer_default_config(self):
        inner_configs = [
            {"id": "inner_x"},
            {"id": "inner_y"},
        ]

        @experiment(configs=inner_configs)
        async def inner(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        @experiment(configs=[])
        async def outer(value: str) -> str:
            await asyncio.sleep(0.01)
            if False:
                await inner(value)
            experiment_case = current_experiment_case.get()
            assert experiment_case is not None
            outer_config_id = experiment_case.get_config_id(outer.__qualname__)
            inner_experiment = experiment_fn_registry.get_experiment(inner)
            inner_result = await inner_experiment(experiment_case, value)
            return f"{outer_config_id}|{inner_result}"

        async with Spearmint.run(outer, await_background_cases=True) as runner:
            results = await runner("test")

        assert results.main_result.result == "default|test_inner_x"
        assert len(results.variant_results) == 1

        variant_values = {r.result for r in results.variant_results}
        assert variant_values == {"default|test_inner_y"}

    @pytest.mark.asyncio
    async def test_variants_not_awaited(self):
        configs = [
            {"id": "main"},
            {"id": "variant_a"},
            {"id": "variant_b"},
        ]

        seen: list[str] = []
        done = asyncio.Event()

        @experiment(configs=configs)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            seen.append(config["id"])
            if len(seen) == len(configs):
                done.set()
            return f"{value}_{config['id']}"

        async with Spearmint.run(process, await_background_cases=False) as runner:
            results = await runner("test")

        assert results.main_result.result == "test_main"
        assert results.variant_results == []

        await asyncio.wait_for(done.wait(), timeout=1.0)
        assert set(seen) == {"main", "variant_a", "variant_b"}