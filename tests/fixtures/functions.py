"""Reusable test functions for integration testing.

These functions simulate common use cases and patterns for Spearmint experiments.
"""

import asyncio
from typing import Any

from spearmint import Config


async def async_echo(value: str, config: Config) -> str:
    """Simple async function that echoes input with config ID.
    
    Args:
        value: Input string to echo
        config: Configuration object
        
    Returns:
        String combining value and config ID
    """
    await asyncio.sleep(0.01)  # Simulate async work
    return f"{value}_{config['id']}"


async def async_multiply(x: int, config: Config) -> int:
    """Async function that multiplies input by config multiplier.
    
    Args:
        x: Input number
        config: Configuration with 'multiplier' field
        
    Returns:
        Result of multiplication
    """
    await asyncio.sleep(0.01)
    multiplier = config.get("multiplier", 2)
    return x * multiplier


def sync_echo(value: str, config: Config) -> str:
    """Synchronous function that echoes input with config ID.
    
    Args:
        value: Input string to echo
        config: Configuration object
        
    Returns:
        String combining value and config ID
    """
    return f"{value}_{config['id']}"


def sync_multiply(x: int, config: Config) -> int:
    """Sync function that multiplies input by config multiplier.
    
    Args:
        x: Input number
        config: Configuration with 'multiplier' field
        
    Returns:
        Result of multiplication
    """
    multiplier = config.get("multiplier", 2)
    return x * multiplier


async def async_add_numbers(a: int, b: int, config: Config) -> int:
    """Async function with multiple non-config parameters.
    
    Args:
        a: First number
        b: Second number
        config: Configuration with optional 'offset' field
        
    Returns:
        Sum with optional offset applied
    """
    await asyncio.sleep(0.01)
    result = a + b
    offset = config.get("offset", 0)
    return result + offset


def sync_concatenate(prefix: str, suffix: str, config: Config) -> str:
    """Sync function with multiple string parameters.
    
    Args:
        prefix: Prefix string
        suffix: Suffix string
        config: Configuration with 'separator' field
        
    Returns:
        Concatenated string with separator
    """
    separator = config.get("separator", "_")
    return f"{prefix}{separator}{suffix}{separator}{config['id']}"


async def async_with_defaults(value: str, multiplier: int = 1, config: Config = None) -> str:
    """Async function with default parameter values.
    
    Args:
        value: Input value
        multiplier: Multiplier with default
        config: Configuration object (will be injected)
        
    Returns:
        Processed string
    """
    await asyncio.sleep(0.01)
    if config:
        config_id = config.get("id", "unknown")
    else:
        config_id = "no_config"
    return f"{value * multiplier}_{config_id}"


async def async_no_config_param(value: str) -> str:
    """Async function without config parameter.
    
    This tests that decorated functions work even without config injection.
    
    Args:
        value: Input value
        
    Returns:
        Processed value
    """
    await asyncio.sleep(0.01)
    return f"processed_{value}"


def sync_no_config_param(value: int) -> int:
    """Sync function without config parameter.
    
    Args:
        value: Input value
        
    Returns:
        Doubled value
    """
    return value * 2


async def async_dict_return(key: str, config: Config) -> dict[str, Any]:
    """Async function that returns a dictionary.
    
    Args:
        key: Dictionary key
        config: Configuration object
        
    Returns:
        Dictionary with key and config info
    """
    await asyncio.sleep(0.01)
    return {
        "key": key,
        "config_id": config["id"],
        "temperature": config.get("temperature", None),
    }


async def async_long_running(duration: float, config: Config) -> str:
    """Async function with configurable sleep duration.
    
    Useful for testing parallel vs sequential execution timing.
    
    Args:
        duration: Sleep duration in seconds
        config: Configuration object
        
    Returns:
        Completion message with config ID
    """
    await asyncio.sleep(duration)
    return f"completed_{config['id']}"


def sync_with_side_effect(value: str, tracker: list, config: Config) -> str:
    """Sync function that records side effects.
    
    Args:
        value: Input value
        tracker: List to append execution info to
        config: Configuration object
        
    Returns:
        Processed value
    """
    tracker.append({"config_id": config["id"], "value": value})
    return f"{value}_{config['id']}"


async def async_with_exception(should_fail: bool, config: Config) -> str:
    """Async function that can raise exceptions.
    
    Args:
        should_fail: Whether to raise an exception
        config: Configuration object
        
    Returns:
        Success message
        
    Raises:
        ValueError: If should_fail is True
    """
    await asyncio.sleep(0.01)
    if should_fail:
        raise ValueError(f"Intentional failure for config {config['id']}")
    return f"success_{config['id']}"
