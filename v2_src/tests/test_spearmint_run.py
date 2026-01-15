import asyncio
from typing import Annotated, Any

import pytest

from spearmint_v2 import Spearmint, Config, experiment


class TestSpearmintRun:
    """Test @configure decorator with a single configuration."""

    @pytest.mark.asyncio
    async def test_spearmint_run(self):
        single_config = [{"id": "single"}]

        @experiment(configs=single_config)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        async with Spearmint.run(process) as runner:
            results = await runner("test")

        assert results.main_result == "test_single"
        assert results.variant_results == []

    @pytest.mark.asyncio
    async def test_spearmint_run_default_binding(self):
        bound_config = [
            {
                "bound": {
                    "config": {
                        "id": "my_bound_config"
                    }
                }
            }
        ]

        # TODO: add Bind type and use it during DI in Spearmint
        @experiment(configs=bound_config)
        async def process(value: str, config: Annotated[Config, Bind("bound.config")]) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        async with Spearmint.run(process) as runner:
            results = await runner("test")

        assert results.main_result == "test_my_bound_config"
        assert results.variant_results == []