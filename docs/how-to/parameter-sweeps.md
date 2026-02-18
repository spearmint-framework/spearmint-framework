# Parameter Sweeps with DynamicValue

Automatically generate multiple configurations from parameter ranges using combinatorial expansion.

## Problem

When testing multiple parameter combinations, manually creating each configuration is tedious and error-prone:

``````python
# Manual approach - tedious!
configs = [
    {"model": "gpt-4", "temperature": 0.1},
    {"model": "gpt-4", "temperature": 0.5},
    {"model": "gpt-4", "temperature": 0.9},
    {"model": "gpt-3.5", "temperature": 0.1},
    {"model": "gpt-3.5", "temperature": 0.5},
    {"model": "gpt-3.5", "temperature": 0.9},
]
``````

## Solution

Use `DynamicValue` to automatically expand parameter ranges into all combinations:

``````python
from spearmint import Spearmint, Config
from spearmint.configuration import DynamicValue

configs = [
    {
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        "temperature": DynamicValue([0.1, 0.5, 0.9]),
    }
]

mint = Spearmint(configs=configs)
# Automatically generates 2 × 3 = 6 configurations!
``````

## Basic Usage

### Simple Parameter Sweep

Sweep over a list of values:

``````python
from spearmint import Spearmint, Config
from spearmint.configuration import DynamicValue

configs = [
    {
        "model": DynamicValue(["gpt-4", "gpt-3.5", "claude-3"]),
        "max_tokens": 100,  # Static value
    }
]

mint = Spearmint(configs=configs)

@mint.experiment()
def generate(config: Config) -> str:
    return f"Using {config['model']}"

if __name__ == "__main__":
    print(f"Generated {len(mint.configs)} configurations")
    # Output: Generated 3 configurations
``````

### Multiple Parameters

Combine multiple dynamic values for cartesian product:

``````python
configs = [
    {
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        "temperature": DynamicValue([0.1, 0.5, 0.9]),
        "max_tokens": 100,  # Static
    }
]

mint = Spearmint(configs=configs)
print(f"Generated {len(mint.configs)} configurations")
# Output: Generated 6 configurations (2 models × 3 temperatures)
``````

## Advanced Usage

### Using Ranges

Use Python's `range()` for numeric sweeps:

``````python
from spearmint.configuration import DynamicValue

configs = [
    {
        "model": "gpt-4",
        "temperature": DynamicValue(range(1, 10, 2)),  # 1, 3, 5, 7, 9
        "learning_rate": DynamicValue([0.001, 0.01, 0.1]),
    }
]
``````

### Using Generators

Any iterable works, including generators:

``````python
def temperature_values():
    """Custom generator for temperature values."""
    for i in range(1, 10):
        yield i / 10.0  # 0.1, 0.2, ..., 0.9

configs = [
    {
        "model": "gpt-4",
        "temperature": DynamicValue(temperature_values()),
    }
]
``````

### Nested Structures

Use `DynamicValue` in nested configurations:

``````python
configs = [
    {
        "llm": {
            "model": DynamicValue(["gpt-4", "gpt-3.5"]),
            "temperature": DynamicValue([0.5, 0.7, 0.9]),
        },
        "retrieval": {
            "top_k": DynamicValue([3, 5, 10]),
        }
    }
]

# Generates 2 × 3 × 3 = 18 configurations
``````

## Complete Example

Here's a full parameter sweep for a machine learning experiment:

``````python
from spearmint import Spearmint, Config
from spearmint.configuration import DynamicValue

# Define parameter sweep
configs = [
    {
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        "temperature": DynamicValue(range(1, 10, 4)),  # 1, 5, 9
        "static_param": "always_same",
    }
]

mint = Spearmint(configs=configs)

@mint.experiment()
def train_model(config: Config) -> str:
    """Train model with given configuration."""
    # Normalize temperature from integer to float
    temp = config['temperature'] / 10.0
    return f"Model={config['model']}, Temp={temp}"

if __name__ == "__main__":
    print(f"Generated {len(mint.configs)} configurations")
    # Output: Generated 6 configurations (2 models × 3 temperatures)
    
    # Run experiment with all configurations
    with Spearmint.run(train_model, await_variants=True) as runner:
        result = runner()
        
        # Main result (first configuration)
        print(f"Main: {result.main_result.result}")
        # Output: Main: Model=gpt-4, Temp=0.1
        
        # All variant results
        for variant in result.variant_results:
            print(f"Variant: {variant.result}")
        # Output: 
        # Variant: Model=gpt-4, Temp=0.5
        # Variant: Model=gpt-4, Temp=0.9
        # Variant: Model=gpt-3.5, Temp=0.1
        # Variant: Model=gpt-3.5, Temp=0.5
        # Variant: Model=gpt-3.5, Temp=0.9
``````

## How It Works

`DynamicValue` expands configurations using a **cartesian product**:

1. **Identify dynamic values**: Find all `DynamicValue` instances in the configuration
2. **Generate combinations**: Create all possible combinations of dynamic values
3. **Create configs**: Generate a separate configuration for each combination

Example expansion:

``````python
# Input configuration
{
    "model": DynamicValue(["A", "B"]),
    "temp": DynamicValue([1, 2]),
    "static": "X"
}

# Expands to 4 configurations:
[
    {"model": "A", "temp": 1, "static": "X"},
    {"model": "A", "temp": 2, "static": "X"},
    {"model": "B", "temp": 1, "static": "X"},
    {"model": "B", "temp": 2, "static": "X"},
]
``````

## Best Practices

### 1. Start Small

Begin with small parameter spaces and scale up:

``````python
# Start with 2 × 2 = 4 configurations
configs = [
    {
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        "temperature": DynamicValue([0.5, 0.9]),
    }
]
``````

### 2. Watch Configuration Count

Be mindful of exponential growth:

``````python
# This creates 3 × 5 × 10 × 4 = 600 configurations!
configs = [
    {
        "param1": DynamicValue(range(3)),
        "param2": DynamicValue(range(5)),
        "param3": DynamicValue(range(10)),
        "param4": DynamicValue(range(4)),
    }
]
``````

### 3. Use with Pydantic

Combine with typed configurations for validation:

``````python
from pydantic import BaseModel, Field
from spearmint.configuration import DynamicValue

class ModelConfig(BaseModel):
    model: str
    temperature: float = Field(ge=0.0, le=2.0)

configs = [
    {
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        "temperature": DynamicValue([0.1, 0.5, 0.9]),
    }
]

@mint.experiment()
def generate(config: ModelConfig) -> str:
    # Config is validated and typed
    return config.model
``````

## Common Patterns

### Grid Search

Test all combinations of hyperparameters:

``````python
configs = [
    {
        "learning_rate": DynamicValue([0.001, 0.01, 0.1]),
        "batch_size": DynamicValue([16, 32, 64]),
        "epochs": DynamicValue([10, 20, 50]),
    }
]
# Creates 3 × 3 × 3 = 27 configurations
``````

### Model Comparison

Compare different models with same parameters:

``````python
configs = [
    {
        "model": DynamicValue(["gpt-4", "gpt-3.5", "claude-3"]),
        "temperature": 0.7,
        "max_tokens": 150,
    }
]
# Creates 3 configurations
``````

### Temperature Sweep

Fine-tune temperature parameter:

``````python
configs = [
    {
        "model": "gpt-4",
        "temperature": DynamicValue([i/10 for i in range(0, 21, 2)]),  # 0.0, 0.2, ..., 2.0
    }
]
# Creates 11 configurations
``````

## See Also

- [Configuration Basics](../tutorials/configuration-basics.md) - Learn configuration fundamentals
- [Typed Configurations](typed-configurations.md) - Use Pydantic with DynamicValue
- [Compare Configurations](compare-configurations.md) - Run and compare sweep results
- [Cookbook: Dynamic Config Example](https://github.com/spearmint-framework/spearmint-framework/blob/main/cookbook/configuration/dynamic_config.py)
