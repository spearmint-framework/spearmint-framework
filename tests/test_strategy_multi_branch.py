"""Tests for MultiBranchStrategy."""

import pytest

from spearmint.branch import BranchContainer
from spearmint.strategies import MultiBranchStrategy


class TestMultiBranchStrategy:
    """Test MultiBranchStrategy execution patterns."""

    @pytest.mark.asyncio
    async def test_multi_branch_all_success(self, sample_configs):
        """MultiBranchStrategy should execute all configs and return BranchContainer."""
        strategy = MultiBranchStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await strategy.run(sample_func, sample_configs, 10)

        assert isinstance(result, BranchContainer)
        assert len(result) == 3

        # Check all branches succeeded
        assert all(b.status == "success" for b in result)

        # Verify outputs
        outputs = [b.output for b in result]
        assert outputs == [11, 15, 20]  # 10+1, 10+5, 10+10

    @pytest.mark.asyncio
    async def test_multi_branch_mixed_failures(self, sample_configs):
        """MultiBranchStrategy should capture both success and failure."""
        strategy = MultiBranchStrategy()

        async def mixed_func(x: int, config: dict) -> int:
            if config["delta"] == 5:
                raise ValueError("Intentional failure")
            return x + config["delta"]

        result = await strategy.run(mixed_func, sample_configs, 10)

        assert len(result) == 3

        # Check status distribution
        successful = result.successful()
        failed = result.failed()
        assert len(successful) == 2
        assert len(failed) == 1

        # Verify failed branch
        assert failed[0].exception_info is not None
        assert "ValueError" in failed[0].exception_info["type"]

    @pytest.mark.asyncio
    async def test_multi_branch_logging_per_branch(self, sample_configs, in_memory_logger):
        """MultiBranchStrategy should log all branches."""
        strategy = MultiBranchStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await strategy.run(sample_func, sample_configs, 10, logger=in_memory_logger)

        # Should log 3 branches
        assert in_memory_logger.get_branch_count() == 3
        assert in_memory_logger.get_run_count() == 3

    @pytest.mark.asyncio
    async def test_multi_branch_empty_configs_raises(self):
        """MultiBranchStrategy should raise ValueError for empty configs."""
        strategy = MultiBranchStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x

        with pytest.raises(ValueError, match="requires at least one config"):
            await strategy.run(sample_func, [], 10)

    @pytest.mark.asyncio
    async def test_multi_branch_single_config(self, single_config):
        """MultiBranchStrategy should work with single config."""
        strategy = MultiBranchStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await strategy.run(sample_func, single_config, 10)

        assert len(result) == 1
        assert result[0].status == "success"
        assert result[0].output == 15

    @pytest.mark.asyncio
    async def test_multi_branch_all_failures(self, sample_configs):
        """MultiBranchStrategy should handle all branches failing."""
        strategy = MultiBranchStrategy()

        async def failing_func(x: int, config: dict) -> int:
            raise ValueError(f"Failure with delta {config['delta']}")

        result = await strategy.run(failing_func, sample_configs, 10)

        assert len(result) == 3
        assert all(b.status == "failed" for b in result)
        assert all(b.exception_info is not None for b in result)

    @pytest.mark.asyncio
    async def test_multi_branch_preserves_config_order(self, sample_configs):
        """MultiBranchStrategy should preserve config order in results."""
        strategy = MultiBranchStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await strategy.run(sample_func, sample_configs, 10)

        # Check config_ids reflect order
        assert result[0].config == {"delta": 1, "multiplier": 2}
        assert result[1].config == {"delta": 5, "multiplier": 3}
        assert result[2].config == {"delta": 10, "multiplier": 1}

    @pytest.mark.asyncio
    async def test_multi_branch_concurrent_execution(self, sample_configs):
        """MultiBranchStrategy should execute branches concurrently."""
        strategy = MultiBranchStrategy()
        execution_order = []

        async def tracking_func(x: int, config: dict) -> int:
            execution_order.append(config["delta"])
            # All start roughly at the same time
            return x + config["delta"]

        await strategy.run(tracking_func, sample_configs, 10)

        # All should have executed (can't strictly test concurrency,
        # but we verify all executed)
        assert len(execution_order) == 3
