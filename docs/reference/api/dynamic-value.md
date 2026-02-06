# DynamicValue

`DynamicValue` enables automatic generation of multiple configurations from iterables, making it easy to create parameter sweeps and grid searches.

## Overview

Instead of manually specifying every configuration combination, use `DynamicValue` to generate them automatically from:
- Lists
- Ranges
- Generator functions
- Any iterable

## Class Definition

``````python
from collections.abc import Iterable
from typing import Generic, TypeVar

T = TypeVar("T")

class DynamicValue(Generic[T]):
    """Represents a value that generates multiple configurations at runtime."""
    
    def __init__(self, values: Iterable[T]) -> None:
        """Initialize with an iterable of values."""
        self.values: Iterable[T] = values
``````

## Basic Usage

### From Lists

``````python
from spearmint import Spearmint
from spearmint.configuration import DynamicValue

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo", "gpt-4o-mini"])
}]

mint = Spearmint(configs=configs)
# Creates 3 configurations:
# {"model": "gpt-4", "config_id": "..."}
# {"model": "gpt-3.5-turbo", "config_id": "..."}
# {"model": "gpt-4o-mini", "config_id": "..."}
``````

### From Ranges

``````python
from spearmint.configuration import DynamicValue

configs = [{
    "temperature": DynamicValue(range(0, 101, 25))  # 0, 25, 50, 75, 100
}]

# Creates 5 configurations with temperature: 0, 25, 50, 75, 100
``````

### From Generators

``````python
from spearmint.configuration import DynamicValue

def temperature_values():
    """Generate temperature values."""
    for temp in range(0, 101, 50):
        yield temp / 100.0  # 0.0, 0.5, 1.0

configs = [{
    "model": "gpt-4",
    "temperature": DynamicValue(temperature_values())
}]

# Creates 3 configurations with temperatures: 0.0, 0.5, 1.0
``````

## Multiple DynamicValues (Cartesian Product)

When multiple `DynamicValue` instances are in one config, Spearmint creates all combinations:

### Example: Model and Temperature Grid

``````python
from spearmint.configuration import DynamicValue

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0])
}]

# Creates 6 configurations (2 models × 3 temperatures):
# {"model": "gpt-4", "temperature": 0.0}
# {"model": "gpt-4", "temperature": 0.5}
# {"model": "gpt-4", "temperature": 0.7}
# {"model": "gpt-3.5-turbo", "temperature": 0.0}
# {"model": "gpt-3.5-turbo", "temperature": 0.5}
# {"model": "gpt-3.5-turbo", "temperature": 1.0}
``````

### Example: Three-Dimensional Grid

``````python
from spearmint.configuration import DynamicValue

configs = [{
    "model": DynamicValue(["gpt-4o", "gpt-4o-mini"]),
    "temperature": DynamicValue([0.0, 0.7]),
    "max_tokens": DynamicValue([500, 1000, 2000])
}]

# Creates 12 configurations (2 × 2 × 3)
``````

## Nested DynamicValues

`DynamicValue` works with nested configuration structures:

``````python
from spearmint.configuration import DynamicValue

configs = [{
    "llm": {
        "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
        "params": {
            "temperature": DynamicValue([0.0, 0.5, 1.0]),
            "max_tokens": 1000
        }
    }
}]

# Creates 6 configurations with nested structure preserved
``````

## Advanced Examples

### Custom Value Generation

``````python
from spearmint.configuration import DynamicValue

def learning_rates():
    """Generate learning rates on log scale."""
    for exp in range(-5, 0):  # 10^-5 to 10^-1
        yield 10 ** exp

configs = [{
    "optimizer": "adam",
    "learning_rate": DynamicValue(learning_rates())
}]
``````

### Conditional Value Generation

``````python
from spearmint.configuration import DynamicValue

def model_specific_temps(model):
    """Different temperature ranges for different models."""
    if model == "gpt-4":
        return [0.0, 0.3, 0.7]
    else:
        return [0.5, 1.0]

# For a single model
configs = [{
    "model": "gpt-4",
    "temperature": DynamicValue(model_specific_temps("gpt-4"))
}]
``````

### Mixing Static and Dynamic

``````python
from spearmint.configuration import DynamicValue

configs = [
    # Static config
    {
        "model": "gpt-4",
        "temperature": 0.7,
        "mode": "production"
    },
    # Dynamic configs
    {
        "model": DynamicValue(["gpt-4o-mini", "gpt-3.5-turbo"]),
        "temperature": DynamicValue([0.0, 0.5, 1.0]),
        "mode": "evaluation"
    }
]

# Creates 7 configurations total:
# 1 static + 6 from dynamic (2 models × 3 temperatures)
``````

## Use Cases

### Parameter Sweep for Tuning

``````python
from spearmint import Spearmint, Config
from spearmint.configuration import DynamicValue

configs = [{
    "model": "gpt-4",
    "temperature": DynamicValue([i * 0.1 for i in range(0, 21)]),  # 0.0 to 2.0
    "top_p": DynamicValue([0.9, 0.95, 1.0]),
    "frequency_penalty": DynamicValue([0.0, 0.5, 1.0])
}]

mint = Spearmint(configs=configs)
# Creates 21 × 3 × 3 = 189 configurations

@mint.experiment()
def evaluate_params(prompt: str, config: Config) -> float:
    response = generate(prompt, **config.root)
    return evaluate_quality(response)
``````

### A/B/n Testing

``````python
from spearmint.configuration import DynamicValue

configs = [{
    "algorithm_version": DynamicValue(["v1", "v2", "v3", "v4"]),
    "feature_flags": {
        "use_cache": True,
        "timeout": 30
    }
}]

# Test 4 algorithm versions with same feature flags
``````

### Model Comparison

``````python
from spearmint.configuration import DynamicValue

configs = [{
    "provider": DynamicValue(["openai", "anthropic", "cohere"]),
    "model": DynamicValue({
        "openai": "gpt-4",
        "anthropic": "claude-3-opus",
        "cohere": "command-r-plus"
    }),
    "temperature": 0.7
}]
``````

## Performance Considerations

### Memory Efficiency

DynamicValues are expanded only once during Spearmint initialization:

``````python
# Generator is consumed once to create all configs
def large_range():
    for i in range(1000000):
        yield i

configs = [{
    "param": DynamicValue(large_range())
}]

# Creates 1,000,000 Config objects immediately
# Consider memory implications for very large sweeps
mint = Spearmint(configs=configs)
``````

### Lazy Evaluation Not Supported

``````python
# DynamicValue is NOT lazy - all configs created upfront
configs = [{
    "model": DynamicValue(range(1000))
}]

mint = Spearmint(configs=configs)
# All 1000 configs are created now, not when experiments run
``````

## Limitations

### Cannot Use in Nested Structures Directly

``````python
# ❌ This won't work as expected
configs = [{
    "params": DynamicValue([
        {"temp": 0.7, "tokens": 100},
        {"temp": 0.9, "tokens": 200}
    ])
}]

# ✅ Instead, use DynamicValue for individual values
configs = [{
    "params": {
        "temp": DynamicValue([0.7, 0.9]),
        "tokens": DynamicValue([100, 200])
    }
}]
``````

### Type Checking

DynamicValue is generic, but type checking is limited:

``````python
from spearmint.configuration import DynamicValue

# Type hint works
temps: DynamicValue[float] = DynamicValue([0.0, 0.5, 1.0])

# But this won't be caught by type checker
mixed: DynamicValue[float] = DynamicValue([0.0, "not a float", 1.0])
``````

## See Also

- [Config Object](config.md) - Configuration structure
- [Config Parsing](config-parsing.md) - Loading and parsing configs
- [Parameter Sweeps How-To](../../how-to/parameter-sweeps.md) - Practical guide
- [Compare Configurations How-To](../../how-to/compare-configurations.md) - Configuration comparison
