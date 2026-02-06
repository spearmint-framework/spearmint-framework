# Working with Configurations

This guide covers common configuration patterns and best practices.

## Configuration Basics

### Dictionary Configurations

The simplest way to define configurations:

```python
from spearmint import Spearmint

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7},
    {"model": "gpt-3.5-turbo", "temperature": 0.5},
])
```

### YAML Configurations

Load configurations from YAML files:

```yaml
# config.yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
system_prompt: "You are a helpful assistant."
```

```python
mint = Spearmint(configs=["config.yaml"])
```

### Directory of Configurations

Load all YAML files from a directory:

```
configs/
├── gpt4.yaml
├── gpt35.yaml
└── claude.yaml
```

```python
mint = Spearmint(configs=["configs/"])
# Loads all three files as separate configurations
```

## Dynamic Configuration Generation

### Using DynamicValue

Generate multiple configurations from iterables:

```python
from spearmint.configuration import DynamicValue

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0])
}]
# Creates 2 × 3 = 6 configurations
```

### With Ranges

```python
configs = [{
    "max_tokens": DynamicValue(range(100, 1001, 100)),
    "temperature": DynamicValue([i/10 for i in range(0, 11)])
}]
# Creates 10 × 11 = 110 configurations
```

### With Generators

```python
def temperature_sweep():
    for i in range(0, 101, 10):
        yield i / 100.0

configs = [{
    "temperature": DynamicValue(temperature_sweep())
}]
# Creates 11 configurations (0.0 to 1.0)
```

### Nested Dynamic Values

```python
configs = [{
    "llm": {
        "model": DynamicValue(["gpt-4", "claude-3"]),
        "temperature": DynamicValue([0.0, 0.5])
    },
    "max_retries": DynamicValue([1, 3])
}]
# Creates 2 × 2 × 3 = 12 configurations
```

## Type-Safe Configurations

### Using Pydantic Models

Define typed configuration models:

```python
from pydantic import BaseModel, Field
from spearmint import Spearmint

class LLMConfig(BaseModel):
    model: str
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, gt=0)

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000}
])

@mint.experiment(bindings={LLMConfig: ""})
def generate(prompt: str, config: LLMConfig) -> str:
    # config is typed with IDE support
    return call_llm(config.model, config.temperature, prompt)
```

### Nested Model Binding

```python
from pydantic import BaseModel

class ModelConfig(BaseModel):
    model: str
    temperature: float

class AppConfig(BaseModel):
    llm: ModelConfig
    timeout: int

configs = [{
    "llm": {
        "model": "gpt-4",
        "temperature": 0.7
    },
    "timeout": 30
}]

mint = Spearmint(configs=configs)

# Bind to nested path
@mint.experiment(bindings={ModelConfig: "llm"})
def generate(prompt: str, config: ModelConfig) -> str:
    return f"{config.model}: {prompt}"
```

### With Validation

```python
from pydantic import BaseModel, validator

class LLMConfig(BaseModel):
    model: str
    temperature: float
    
    @validator('model')
    def validate_model(cls, v):
        allowed = ['gpt-4', 'gpt-3.5-turbo', 'claude-3']
        if v not in allowed:
            raise ValueError(f"Model must be one of {allowed}")
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
```

## Configuration Organization

### Environment-Based Configurations

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

### Base + Override Pattern

```yaml
# base.yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
```

```python
from spearmint import Spearmint
import yaml

# Load base config
with open("base.yaml") as f:
    base_config = yaml.safe_load(f)

# Override specific values
test_configs = [
    {**base_config, "temperature": 0.0},
    {**base_config, "temperature": 0.5},
    {**base_config, "temperature": 1.0},
]

mint = Spearmint(configs=test_configs)
```

### Feature Flags in Configs

```python
configs = [{
    "model": "gpt-4",
    "features": {
        "use_cache": True,
        "enable_logging": True,
        "experimental_mode": False
    }
}]

@mint.experiment()
def process(input: str, config: dict) -> str:
    if config["features"]["use_cache"]:
        # Use cached results
        ...
    return result
```

## Configuration Identifiers

### Auto-Generated IDs

Spearmint auto-generates config IDs:

```python
configs = [
    {"model": "gpt-4"},  # config_id: auto-generated
]
```

### Custom IDs

Provide explicit IDs for tracking:

```python
configs = [
    {"config_id": "baseline", "model": "gpt-3.5-turbo"},
    {"config_id": "premium", "model": "gpt-4"},
    {"config_id": "experimental", "model": "gpt-5-beta"},
]
```

### Descriptive IDs

Use descriptive names for clarity:

```python
configs = [
    {
        "config_id": "prod-gpt4-conservative",
        "model": "gpt-4",
        "temperature": 0.0
    },
    {
        "config_id": "prod-gpt4-creative",
        "model": "gpt-4",
        "temperature": 0.9
    },
]
```

## Common Patterns

### Pattern 1: A/B Testing

```python
configs = [
    {"config_id": "variant-a", "algorithm": "v1", "threshold": 0.5},
    {"config_id": "variant-b", "algorithm": "v2", "threshold": 0.7},
]

mint = Spearmint(configs=configs)

@mint.experiment()
def process_request(data: dict, config: dict) -> dict:
    return run_algorithm(
        config["algorithm"],
        data,
        config["threshold"]
    )
```

### Pattern 2: Hyperparameter Tuning

```python
from spearmint.configuration import DynamicValue

configs = [{
    "learning_rate": DynamicValue([0.001, 0.01, 0.1]),
    "batch_size": DynamicValue([16, 32, 64]),
    "epochs": DynamicValue([10, 20, 50])
}]
# Creates 3 × 3 × 3 = 27 configurations

mint = Spearmint(configs=configs)
```

### Pattern 3: Model Comparison

```python
configs = [
    {
        "config_id": "openai-gpt4",
        "provider": "openai",
        "model": "gpt-4",
        "cost_per_1k_tokens": 0.03
    },
    {
        "config_id": "anthropic-claude3",
        "provider": "anthropic",
        "model": "claude-3-opus",
        "cost_per_1k_tokens": 0.015
    },
]
```

### Pattern 4: Progressive Rollout

```python
configs = [
    {
        "config_id": "stable-v1",
        "version": "1.0.0",
        "rollout_percentage": 90
    },
    {
        "config_id": "canary-v2",
        "version": "2.0.0-beta",
        "rollout_percentage": 10
    },
]
```

## Best Practices

### 1. Keep Configurations Simple

Start with simple dictionaries:

```python
# Good
configs = [{"model": "gpt-4"}]

# Overkill for simple use cases
class ComplexConfig(BaseModel):
    model: str
    temperature: float
    # ... 20 more fields
```

### 2. Use Type Safety for Complex Configs

```python
# Good for complex configurations
class DetailedConfig(BaseModel):
    model: str
    temperature: float
    retry_config: RetryConfig
    timeout_config: TimeoutConfig
    feature_flags: FeatureFlags
```

### 3. Avoid Configuration Explosion

```python
# Careful - creates 1,000,000 configurations!
configs = [{
    "a": DynamicValue(range(100)),
    "b": DynamicValue(range(100)),
    "c": DynamicValue(range(100))
}]

# Better - create configurations deliberately
configs = [{
    "a": DynamicValue([0, 50, 100]),
    "b": DynamicValue([0, 50, 100]),
    "c": DynamicValue([0, 50, 100])
}]  # Only 27 configurations
```

### 4. Use Meaningful Names

```python
# Good
configs = [
    {"config_id": "prod-high-accuracy", "temperature": 0.0},
    {"config_id": "prod-balanced", "temperature": 0.5},
]

# Bad
configs = [
    {"config_id": "c1", "temperature": 0.0},
    {"config_id": "c2", "temperature": 0.5},
]
```

### 5. Document Configuration Schema

```python
# configs/schema.md
"""
Configuration Schema

Required fields:
- model (str): Model identifier
- temperature (float): 0.0 to 2.0

Optional fields:
- max_tokens (int): Default 1000
- system_prompt (str): Default ""
"""
```

### 6. Version Your Configurations

```yaml
# config.yaml
version: "1.0.0"
model: gpt-4
temperature: 0.7
```

## Troubleshooting

### Config Not Found

```python
# Error: KeyError: 'model'
@mint.experiment()
def process(input: str, config: dict) -> str:
    return config["model"]  # Key doesn't exist

# Solution: Use get() with defaults
@mint.experiment()
def process(input: str, config: dict) -> str:
    return config.get("model", "gpt-3.5-turbo")
```

### Type Binding Errors

```python
# Error: Pydantic validation failed
@mint.experiment(bindings={LLMConfig: ""})
def process(input: str, config: LLMConfig) -> str:
    return config.model

# Solution: Ensure config matches model schema
configs = [
    {"model": "gpt-4", "temperature": 0.7}  # All required fields
]
```

### YAML Loading Errors

```python
# Error: FileNotFoundError
mint = Spearmint(configs=["missing.yaml"])

# Solution: Check file exists
from pathlib import Path

config_path = Path("config.yaml")
if config_path.exists():
    mint = Spearmint(configs=[config_path])
else:
    mint = Spearmint(configs=[{"model": "gpt-4"}])  # Fallback
```

## See Also

- [Configuration API Reference](../reference/api/configuration.md)
- [Core Concepts](../getting-started/concepts.md)
- [Quick Start](../getting-started/quickstart.md)
