"""Tests for RoundRobinStrategy."""

import pytest

from spearmint.strategies import RoundRobinStrategy


class TestRoundRobinStrategy:
    """Test RoundRobinStrategy execution patterns."""

    @pytest.mark.asyncio
    async def test_round_robin_cycles_configs(self, sample_configs):
        """RoundRobinStrategy should cycle through configs on successive calls."""
        strategy = RoundRobinStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        # First call should use config 0
        result1 = await strategy.run(sample_func, sample_configs, 10)
        assert result1 == 11  # 10 + 1

        # Second call should use config 1
        result2 = await strategy.run(sample_func, sample_configs, 10)
        assert result2 == 15  # 10 + 5

        # Third call should use config 2
        result3 = await strategy.run(sample_func, sample_configs, 10)
        assert result3 == 20  # 10 + 10

        # Fourth call should cycle back to config 0
        result4 = await strategy.run(sample_func, sample_configs, 10)
        assert result4 == 11  # 10 + 1

    @pytest.mark.asyncio
    async def test_round_robin_failure_propagates(self, sample_configs):
        """RoundRobinStrategy should propagate exceptions from function."""
        strategy = RoundRobinStrategy()

        async def failing_func(x: int, config: dict) -> int:
            if config["delta"] == 5:
                raise ValueError("Intentional failure")
            return x + config["delta"]

        # First call succeeds (delta=1)
        result = await strategy.run(failing_func, sample_configs, 10)
        assert result == 11

        # Second call should fail (delta=5)
        with pytest.raises(RuntimeError, match="ValueError: Intentional failure"):
            await strategy.run(failing_func, sample_configs, 10)

        # Third call succeeds (delta=10, index advanced despite failure)
        result = await strategy.run(failing_func, sample_configs, 10)
        assert result == 20

    @pytest.mark.asyncio
    async def test_round_robin_logs_branch(self, sample_configs, in_memory_logger):
        """RoundRobinStrategy should log each execution."""
        strategy = RoundRobinStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        # Execute with logger
        await strategy.run(sample_func, sample_configs, 10, logger=in_memory_logger)

        # Verify logging
        assert in_memory_logger.get_run_count() == 1
        assert in_memory_logger.get_branch_count() == 1

        # Execute again
        await strategy.run(sample_func, sample_configs, 10, logger=in_memory_logger)

        # Should have 2 runs, 2 branches
        assert in_memory_logger.get_run_count() == 2
        assert in_memory_logger.get_branch_count() == 2

    @pytest.mark.asyncio
    async def test_round_robin_empty_configs_raises(self):
        """RoundRobinStrategy should raise ValueError for empty configs."""
        strategy = RoundRobinStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x

        with pytest.raises(ValueError, match="requires at least one config"):
            await strategy.run(sample_func, [], 10)

    @pytest.mark.asyncio
    async def test_round_robin_single_config(self, single_config):
        """RoundRobinStrategy should work with single config."""
        strategy = RoundRobinStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        # All calls should use the same config
        result1 = await strategy.run(sample_func, single_config, 10)
        assert result1 == 15

        result2 = await strategy.run(sample_func, single_config, 10)
        assert result2 == 15

    @pytest.mark.asyncio
    async def test_round_robin_logs_failure(self, sample_configs, in_memory_logger):
        """RoundRobinStrategy should log failed branches."""
        strategy = RoundRobinStrategy()

        async def failing_func(x: int, config: dict) -> int:
            raise ValueError("Test error")

        # Execute with logger (should fail)
        with pytest.raises(RuntimeError):
            await strategy.run(failing_func, sample_configs, 10, logger=in_memory_logger)

        # Verify branch was logged with failure status
        assert in_memory_logger.get_branch_count() == 1
        branch = in_memory_logger.branches["round_robin_0"][0]
        assert branch.status == "failed"
        assert branch.exception_info is not None
        assert "ValueError" in branch.exception_info["type"]
