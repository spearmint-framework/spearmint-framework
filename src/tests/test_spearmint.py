import asyncio
import runpy
import sys
import threading
from pathlib import Path
from typing import Annotated, Iterable

import pytest
from pydantic import BaseModel

from spearmint import Config, Spearmint, experiment
from spearmint.configuration import Bind
from spearmint.context import current_experiment_case
from spearmint.registry import experiment_fn_registry


class TestSpearmint:
    """Test @configure decorator with a single configuration."""

    def test_basic_experiment(self):
        single_config = [{"id": "single"}]

        @experiment(configs=single_config)
        def process(value: str, config: Config) -> str:
            return f"{value}_{config['id']}"

        with Spearmint.run(process) as runner:
            results = runner("test")

        assert results.main_result.result == "test_single"
        assert results.variant_results == []

    def test_experiment_default_binding(self):
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
        def process(value: str, config: Annotated[Config, Bind("bound.config")]) -> str:
            return f"{value}_{config['id']}"

        # Test direct call with DI
        result = process("test")
        assert result == "test_my_bound_config"

        # Test via Spearmint.run
        with Spearmint.run(process) as runner:
            results = runner("test")

        assert results.main_result.result == "test_my_bound_config"
        assert results.variant_results == []

    def test_experiment_no_configs(self):
        @experiment(configs=[])
        def process(value: str) -> str:
            return f"{value}_no_config"

        result = process("test")
        assert result == "test_no_config"

        with Spearmint.run(process) as runner:
            results = runner("test")

        assert results.main_result.result == "test_no_config"
        assert results.variant_results == []

    def test_typed_config_injection_pydantic_model(self):
        class ModelConfig(BaseModel):
            model_name: str
            temperature: float
            max_tokens: int = 100

        configs = [
            {"model_name": "gpt-4", "temperature": 0.5},
            {"model_name": "gpt-3.5", "temperature": 0.9, "max_tokens": 50},
        ]

        @experiment(configs=configs)
        def generate(prompt: str, model_config: ModelConfig) -> str:
            return (
                f"Prompt: {prompt}, Model: {model_config.model_name}, "
                f"Temp: {model_config.temperature}, MaxTokens: {model_config.max_tokens}"
            )

        with Spearmint.run(generate, await_variants=True) as runner:
            results = runner("Test prompt")

        assert (
            results.main_result.result
            == "Prompt: Test prompt, Model: gpt-4, Temp: 0.5, MaxTokens: 100"
        )
        variant_values = {r.result for r in results.variant_results}
        assert (
            "Prompt: Test prompt, Model: gpt-3.5, Temp: 0.9, MaxTokens: 50"
            in variant_values
        )

    def test_nested_experiments_multiple_configs(self):
        inner_configs = [
            {"id": "inner_a"},
            {"id": "inner_b"},
        ]
        outer_configs = [
            {"id": "outer_a"},
            {"id": "outer_b"},
        ]

        @experiment(configs=inner_configs)
        def inner(value: str, config: Config) -> str:
            return f"{value}_{config['id']}"

        @experiment(configs=outer_configs)
        def outer(value: str, config: Config) -> str:
            inner_result = inner(value)
            return f"{config['id']}|{inner_result}"

        with Spearmint.run(outer, await_variants=True) as runner:
            results = runner("test")

        assert results.main_result.result == "outer_a|test_inner_a"
        assert len(results.variant_results) == 3

        variant_values = {r.result for r in results.variant_results}
        assert variant_values == {
            "outer_a|test_inner_b",
            "outer_b|test_inner_a",
            "outer_b|test_inner_b",
        }

    def test_nested_experiment_outer_default_config(self):
        inner_configs = [
            {"id": "inner_x"},
            {"id": "inner_y"},
        ]

        @experiment(configs=inner_configs)
        def inner(value: str, config: Config) -> str:
            return f"{value}_{config['id']}"

        @experiment(configs=[])
        def outer(value: str) -> str:
            if False:
                inner(value)
            experiment_case = current_experiment_case.get()
            assert experiment_case is not None
            outer_config_id = experiment_case.get_config_id(outer.__qualname__)
            inner_experiment = experiment_fn_registry.get_experiment(inner)
            inner_result = inner_experiment(experiment_case, value)
            return f"{outer_config_id}|{inner_result}"

        with Spearmint.run(outer, await_variants=True) as runner:
            results = runner("test")

        assert results.main_result.result == "default|test_inner_x"
        assert len(results.variant_results) == 1

        variant_values = {r.result for r in results.variant_results}
        assert variant_values == {"default|test_inner_y"}

    def test_variants_not_awaited(self):
        configs = [
            {"id": "main"},
            {"id": "variant_a"},
            {"id": "variant_b"},
        ]

        seen: list[str] = []
        done = threading.Event()

        @experiment(configs=configs)
        def process(value: str, config: Config) -> str:
            seen.append(config["id"])
            if len(seen) == len(configs):
                done.set()
            return f"{value}_{config['id']}"

        with Spearmint.run(process, await_variants=False) as runner:
            results = runner("test")

        assert results.main_result.result == "test_main"
        assert results.variant_results == []

        assert done.wait(timeout=1.0)
        assert set(seen) == {"main", "variant_a", "variant_b"}

    def test_async_experiment_from_sync(self):
        configs = [{"id": "async"}]

        @experiment(configs=configs)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        with Spearmint.run(process) as runner:
            results = runner("test")

        assert results.main_result.result == "test_async"
        assert results.variant_results == []

    @pytest.mark.asyncio
    async def test_async_experiment(self):
        configs = [{"id": "async"}]

        @experiment(configs=configs)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            return f"{value}_{config['id']}"

        result = await process("test")
        assert result == "test_async"

        async with Spearmint.arun(process) as runner:
            results = await runner("test")

        assert results.main_result.result == "test_async"
        assert results.variant_results == []

    @pytest.mark.asyncio
    async def test_async_background_variant_exception_handling(self):
        """Test that exceptions in async background variants don't cause unobserved task warnings."""
        configs = [
            {"id": "main"},
            {"id": "failing_variant"},
        ]

        task_completed = asyncio.Event()

        @experiment(configs=configs)
        async def process(value: str, config: Config) -> str:
            await asyncio.sleep(0.01)
            if config["id"] == "failing_variant":
                try:
                    raise ValueError(f"Test exception in {config['id']}")
                finally:
                    task_completed.set()
            return f"{value}_{config['id']}"

        async with Spearmint.arun(process, await_variants=False) as runner:
            results = await runner("test")

            # Main result should succeed
            assert results.main_result.result == "test_main"
            assert results.variant_results == []

            # Wait for background task to complete (with timeout)
            await asyncio.wait_for(task_completed.wait(), timeout=1.0)

        # If we get here without "Task exception was never retrieved" warnings,
        # the exception handling is working correctly


def _iter_cookbook_scripts() -> Iterable[Path]:
    repo_root = Path(__file__).resolve().parents[2]
    cookbook_root = repo_root / "cookbook"
    excluded_dirs = {"online_experiments", "__pycache__"}

    paths = []
    for path in cookbook_root.rglob("*.py"):
        if any(part in excluded_dirs for part in path.parts):
            continue
        paths.append(path)

    return sorted(paths)


@pytest.mark.parametrize(
    "script_path",
    _iter_cookbook_scripts(),
    ids=lambda path: path.relative_to(Path(__file__).resolve().parents[2]).as_posix(),
)
def test_cookbook_samples(script_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "src"

    monkeypatch.chdir(repo_root)

    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    runpy.run_path(str(script_path), run_name="__main__")
