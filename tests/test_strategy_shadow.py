"""Tests for ShadowStrategy."""

import asyncio

import pytest

from spearmint.strategies import ShadowStrategy


class TestShadowStrategy:
    """Test ShadowStrategy execution patterns."""

    @pytest.mark.asyncio
    async def test_shadow_returns_primary_immediately(self, sample_configs):
        """ShadowStrategy should return primary result immediately."""
        strategy = ShadowStrategy(primary_index=0)

        async def sample_func(x: int, config: dict) -> int:
            # Add small delay to shadow configs
            if config["delta"] != 1:
                await asyncio.sleep(0.1)
            return x + config["delta"]

        # Should return immediately with primary (delta=1)
        result = await strategy.run(sample_func, sample_configs, 10)
        assert result == 11

        # Wait for shadows to complete
        await strategy.gather_shadows()

    @pytest.mark.asyncio
    async def test_shadow_strategy_shadow_failures_dont_affect_primary(self, sample_configs):
        """Shadow failures should not affect primary result."""
        strategy = ShadowStrategy(primary_index=0)

        async def mixed_func(x: int, config: dict) -> int:
            if config["delta"] == 5:  # Second config fails
                raise ValueError("Shadow failure")
            return x + config["delta"]

        # Primary succeeds, returns immediately
        result = await strategy.run(mixed_func, sample_configs, 10)
        assert result == 11

        # Shadows should complete (one fails, one succeeds)
        shadow_branches = await strategy.gather_shadows()
        assert len(shadow_branches) == 2

        # Check that one shadow failed
        failed_branches = [b for b in shadow_branches if b.status == "failed"]
        assert len(failed_branches) == 1

    @pytest.mark.asyncio
    async def test_shadow_strategy_logging_all_branches(self, sample_configs, in_memory_logger):
        """ShadowStrategy should log all branches including shadows."""
        strategy = ShadowStrategy(primary_index=0)

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        # Execute with logger
        result = await strategy.run(sample_func, sample_configs, 10, logger=in_memory_logger)
        assert result == 11

        # Wait for shadows
        await strategy.gather_shadows()

        # Should log primary + 2 shadows = 3 branches total
        assert in_memory_logger.get_branch_count() == 3

    @pytest.mark.asyncio
    async def test_shadow_primary_failure_propagates(self, sample_configs):
        """Primary failure should propagate immediately."""
        strategy = ShadowStrategy(primary_index=0)

        async def failing_func(x: int, config: dict) -> int:
            if config["delta"] == 1:  # Primary fails
                raise ValueError("Primary failure")
            return x + config["delta"]

        with pytest.raises(RuntimeError, match="ValueError: Primary failure"):
            await strategy.run(failing_func, sample_configs, 10)

    @pytest.mark.asyncio
    async def test_shadow_empty_configs_raises(self):
        """ShadowStrategy should raise ValueError for empty configs."""
        strategy = ShadowStrategy()

        async def sample_func(x: int, config: dict) -> int:
            return x

        with pytest.raises(ValueError, match="requires at least one config"):
            await strategy.run(sample_func, [], 10)

    @pytest.mark.asyncio
    async def test_shadow_invalid_primary_index(self, sample_configs):
        """ShadowStrategy should raise for invalid primary index."""
        strategy = ShadowStrategy(primary_index=10)

        async def sample_func(x: int, config: dict) -> int:
            return x

        with pytest.raises(ValueError, match="out of range"):
            await strategy.run(sample_func, sample_configs, 10)

    @pytest.mark.asyncio
    async def test_shadow_single_config_no_shadows(self, single_config):
        """ShadowStrategy with single config should have no shadows."""
        strategy = ShadowStrategy(primary_index=0)

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await strategy.run(sample_func, single_config, 10)
        assert result == 15

        # Should have no shadow tasks
        shadow_branches = await strategy.gather_shadows()
        assert len(shadow_branches) == 0

    @pytest.mark.asyncio
    async def test_shadow_different_primary_index(self, sample_configs):
        """ShadowStrategy should respect custom primary_index."""
        strategy = ShadowStrategy(primary_index=1)

        async def sample_func(x: int, config: dict) -> int:
            return x + config["delta"]

        # Should use config at index 1 (delta=5)
        result = await strategy.run(sample_func, sample_configs, 10)
        assert result == 15

        # Wait for shadows (indices 0 and 2)
        shadow_branches = await strategy.gather_shadows()
        assert len(shadow_branches) == 2
