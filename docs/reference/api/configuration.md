# Configuration API Reference

The configuration module handles configuration parsing, expansion, and management.

## Classes

### `Config`

A dictionary-like wrapper for configuration data.

```python
class Config(RootModel[dict[str, Any]]):
    root: dict[str, Any]
```

`Config` is a Pydantic model that wraps configuration dictionaries, providing validation and easy access.

#### Usage

```python
from spearmint.configuration import Config

# Create from dict
config = Config({"model": "gpt-4", "temperature": 0.7})

# Access like a dict
model = config["model"]

# Iterate
for key, value in config.items():
    print(f"{key}: {value}")
```

#### Methods

`Config` supports standard dictionary operations:
- `config[key]` - Get value
- `config.get(key, default)` - Get with default
- `key in config` - Check membership
- `config.items()` - Iterate key-value pairs
- `config.keys()` - Get keys
- `config.values()` - Get values

### `DynamicValue`

Generate multiple configurations from iterables.

```python
class DynamicValue:
    def __init__(self, iterable: Iterable[Any]) -> None
```

#### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `iterable` | `Iterable[Any]` | Any iterable (list, range, generator) that yields configuration values. |

#### Usage

```python
from spearmint.configuration import DynamicValue

# From list
configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"])
}]
# Creates 2 configurations

# From range
configs = [{
    "temperature": DynamicValue([i/10 for i in range(0, 11)])
}]
# Creates 11 configurations (0.0 to 1.0)

# From generator
def temperature_generator():
    for i in range(0, 101, 25):
        yield i / 100.0

configs = [{
    "temperature": DynamicValue(temperature_generator())
}]
# Creates 5 configurations (0.0, 0.25, 0.5, 0.75, 1.0)

# Combined (Cartesian product)
configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0]),
    "max_tokens": DynamicValue([100, 500, 1000])
}]
# Creates 2 × 3 × 3 = 18 configurations
```

#### Nested DynamicValue

```python
configs = [{
    "llm": {
        "model": DynamicValue(["gpt-4", "claude-3"]),
        "temperature": DynamicValue([0.0, 0.5])
    },
    "max_retries": DynamicValue([1, 3, 5])
}]
# Creates 2 × 2 × 3 = 12 configurations
```

### `Bind`

Specify binding path for Pydantic models in experiment functions.

```python
class Bind:
    def __init__(self, path: str) -> None
```

#### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Dot-separated path to the configuration subset. Empty string for root. |

#### Usage

```python
from spearmint import Spearmint
from spearmint.configuration import Bind
from pydantic import BaseModel

class LLMConfig(BaseModel):
    model: str
    temperature: float

configs = [{
    "llm": {
        "config": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
}]

mint = Spearmint(configs=configs)

# Bind to nested path
@mint.experiment(bindings={LLMConfig: "llm.config"})
def generate(prompt: str, config: LLMConfig) -> str:
    return f"{config.model}: {prompt}"
```

## Functions

### `parse_configs()`

Parse and expand configuration inputs into Config objects.

```python
def parse_configs(
    configs: Sequence[Any],
    config_handler: Callable[[str | Path], list[dict[str, Any]]]
) -> list[Config]
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `configs` | `Sequence[Any]` | List of configurations (dicts, Pydantic models, file paths). |
| `config_handler` | `Callable` | Function to load configurations from file paths. |

#### Returns

`list[Config]` - Expanded list of Config objects.

#### Usage

This function is primarily used internally by Spearmint but can be called directly:

```python
from spearmint.configuration import parse_configs
from spearmint.utils.handlers import yaml_handler

configs = parse_configs(
    [
        {"model": "gpt-4"},
        "config.yaml",
        Path("configs/")
    ],
    yaml_handler
)
```

### `generate_configurations()`

Generate multiple configurations from a template with DynamicValue entries.

```python
def generate_configurations(config: dict[str, Any]) -> list[Config]
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `dict[str, Any]` | Configuration template containing DynamicValue instances. |

#### Returns

`list[Config]` - All possible configurations (Cartesian product).

#### Usage

```python
from spearmint.configuration import generate_configurations, DynamicValue

template = {
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5])
}

configs = generate_configurations(template)
# Returns 4 Config objects:
# 1. {"model": "gpt-4", "temperature": 0.0}
# 2. {"model": "gpt-4", "temperature": 0.5}
# 3. {"model": "gpt-3.5-turbo", "temperature": 0.0}
# 4. {"model": "gpt-3.5-turbo", "temperature": 0.5}
```

#### Nested Expansion

```python
template = {
    "llm": {
        "model": DynamicValue(["a", "b"]),
        "temp": DynamicValue([0.0, 1.0])
    },
    "retries": DynamicValue([1, 3])
}

configs = generate_configurations(template)
# Returns 2 × 2 × 2 = 8 configurations
```

## Configuration Binding

### Basic Binding

Bind Pydantic models to configuration subsets:

```python
from pydantic import BaseModel
from spearmint import Spearmint

class ModelConfig(BaseModel):
    model: str
    temperature: float

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7}
])

# Bind to root (empty string path)
@mint.experiment(bindings={ModelConfig: ""})
def process(input: str, config: ModelConfig) -> str:
    # config is a typed ModelConfig instance
    return f"{config.model}: {input}"
```

### Nested Binding

```python
configs = [{
    "api": {
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
}]

mint = Spearmint(configs=configs)

# Bind to nested path using dot notation
@mint.experiment(bindings={ModelConfig: "api.llm"})
def process(input: str, config: ModelConfig) -> str:
    return f"{config.model}: {input}"
```

### Multiple Bindings

Bind different models to different paths:

```python
from pydantic import BaseModel

class LLMConfig(BaseModel):
    model: str
    temperature: float

class DatabaseConfig(BaseModel):
    host: str
    port: int

configs = [{
    "llm": {"model": "gpt-4", "temperature": 0.7},
    "db": {"host": "localhost", "port": 5432}
}]

mint = Spearmint(configs=configs)

# Currently only single binding supported per function
# Multiple bindings would require enhanced API
```

## Configuration Files

### YAML Format

```yaml
# config.yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
nested:
  value: 42
  list:
    - item1
    - item2
```

### Loading Files

```python
from spearmint import Spearmint

# Single file
mint = Spearmint(configs=["config.yaml"])

# Multiple files
mint = Spearmint(configs=[
    "config1.yaml",
    "config2.yaml"
])

# Directory (loads all .yaml/.yml files)
mint = Spearmint(configs=["configs/"])

# Mixed
mint = Spearmint(configs=[
    {"model": "gpt-4"},  # Dict
    "config.yaml",       # File
    "configs/"           # Directory
])
```

### Directory Structure

```
configs/
├── base.yaml
├── dev.yaml
└── prod.yaml
```

```python
mint = Spearmint(configs=["configs/"])
# Loads all three YAML files as separate configurations
```

## Best Practices

### 1. Use DynamicValue for Parameter Sweeps

```python
configs = [{
    "temperature": DynamicValue([i/10 for i in range(0, 11)]),
    "top_p": DynamicValue([0.9, 0.95, 1.0])
}]
# Systematic parameter exploration
```

### 2. Use Binding for Complex Configs

```python
class ComplexConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int
    retry_config: RetryConfig
    timeout: float

@mint.experiment(bindings={ComplexConfig: ""})
def process(input: str, config: ComplexConfig) -> str:
    # IDE autocomplete, type checking
    return call_api(config)
```

### 3. Use Config IDs for Tracking

```python
configs = [
    {"config_id": "baseline", "model": "gpt-3.5-turbo"},
    {"config_id": "premium", "model": "gpt-4"},
]
# Explicit IDs for better logging and debugging
```

### 4. Organize Config Files by Environment

```
configs/
├── development.yaml
├── staging.yaml
└── production.yaml
```

```python
import os
env = os.getenv("ENV", "development")
mint = Spearmint(configs=[f"configs/{env}.yaml"])
```

## Examples

### Example 1: Simple Grid Search

```python
from spearmint import Spearmint
from spearmint.configuration import DynamicValue

mint = Spearmint(configs=[{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.3, 0.7, 1.0]),
}])
# 2 × 4 = 8 configurations

@mint.experiment()
def evaluate(prompt: str, config: dict) -> str:
    return call_llm(config['model'], config['temperature'], prompt)
```

### Example 2: Typed Configuration

```python
from pydantic import BaseModel, Field
from spearmint import Spearmint

class LLMConfig(BaseModel):
    model: str = Field(..., description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, gt=0)

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000}
])

@mint.experiment(bindings={LLMConfig: ""})
def generate(prompt: str, config: LLMConfig) -> str:
    # Validated, typed config with IDE support
    return call_llm(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        prompt=prompt
    )
```

### Example 3: Loading from Files

```yaml
# config.yaml
model: gpt-4
temperature: 0.7
system_prompt: "You are a helpful assistant."
```

```python
from spearmint import Spearmint

mint = Spearmint(configs=["config.yaml"])

@mint.experiment()
def chat(user_message: str, config: dict) -> str:
    return call_chat_api(
        model=config['model'],
        system=config['system_prompt'],
        user=user_message
    )
```

## See Also

- [Spearmint Class API](spearmint.md) - Main framework class
- [Core Concepts](../../getting-started/concepts.md) - Configuration concepts
- [How-To: Configurations](../../how-to/configurations.md) - Practical guides
