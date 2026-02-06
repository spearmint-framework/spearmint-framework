# Configuration System

Comprehensive guide to Spearmint's configuration system.

## Overview

Spearmint's configuration system provides:
- Multiple input formats (dict, YAML, JSONL)
- Dynamic value expansion for parameter sweeps
- Type-safe binding to Pydantic models
- Nested path access with dot notation

---

## Configuration Sources

### Python Dictionaries

The simplest way to define configs:

``````python
config = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
}

mint = Spearmint(configs=[config])
``````

### YAML Files

Load configurations from YAML files:

**config.yaml:**
``````yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
``````

**Python:**
``````python
mint = Spearmint(configs=["config.yaml"])
``````

### YAML Directories

Load all YAML files from a directory:

``````python
# Loads all .yaml and .yml files in configs/
mint = Spearmint(configs=["configs/"])
``````

Directory structure:
``````
configs/
├── gpt4.yaml
├── gpt35.yaml
└── claude.yaml
``````

### JSONL Files

Load configurations from JSONL (one JSON object per line):

**data.jsonl:**
``````jsonl
{"model": "gpt-4", "temperature": 0.0}
{"model": "gpt-4", "temperature": 0.5}
{"model": "gpt-3.5-turbo", "temperature": 0.7}
``````

**Python:**
``````python
mint = Spearmint(configs=["data.jsonl"])
``````

### Mixed Sources

Combine multiple sources:

``````python
mint = Spearmint(configs=[
    {"model": "gpt-4"},           # Dict
    "config.yaml",                 # Single file
    "configs/",                    # Directory
    "experiments.jsonl"            # JSONL file
])
``````

---

## Dynamic Value Expansion

`DynamicValue` enables parameter sweeps via cartesian product expansion.

### Basic Usage

``````python
from spearmint.config import DynamicValue

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0])
}]

mint = Spearmint(configs=configs)
# Creates 6 configs: 2 models × 3 temperatures
``````

**Expanded configs:**
``````python
[
    {"model": "gpt-4", "temperature": 0.0},
    {"model": "gpt-4", "temperature": 0.5},
    {"model": "gpt-4", "temperature": 1.0},
    {"model": "gpt-3.5-turbo", "temperature": 0.0},
    {"model": "gpt-3.5-turbo", "temperature": 0.5},
    {"model": "gpt-3.5-turbo", "temperature": 1.0},
]
``````

### With Ranges

``````python
configs = [{
    "max_tokens": DynamicValue(range(100, 501, 100))
}]
# Creates configs with max_tokens: 100, 200, 300, 400, 500
``````

### With Generators

``````python
def temperature_generator():
    for temp in range(0, 101, 25):
        yield temp / 100.0

configs = [{
    "temperature": DynamicValue(temperature_generator())
}]
# Creates configs with temperatures: 0.0, 0.25, 0.5, 0.75, 1.0
``````

### Nested Dynamic Values

``````python
configs = [{
    "llm": {
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        "temperature": DynamicValue([0.0, 0.5])
    },
    "max_retries": DynamicValue([1, 3, 5])
}]
# Creates 12 configs: 2 models × 2 temps × 3 retries
``````

---

## Type-Safe Configuration Binding

Bind configuration paths to Pydantic models for type safety.

### Basic Binding

``````python
from pydantic import BaseModel
from typing import Annotated
from spearmint.config import Bind

class LLMConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int = 1000

configs = [{
    "model": "gpt-4",
    "temperature": 0.7
}]

mint = Spearmint(configs=configs)

@mint.experiment()
def generate(
    prompt: str,
    config: Annotated[LLMConfig, Bind("")]  # "" = root level
) -> str:
    # config is typed as LLMConfig
    return f"{config.model}: {prompt}"
``````

### Nested Binding

``````python
class ModelConfig(BaseModel):
    model: str
    temperature: float

configs = [{
    "llm": {
        "settings": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
}]

@mint.experiment()
def generate(
    prompt: str,
    config: Annotated[ModelConfig, Bind("llm.settings")]
) -> str:
    return f"{config.model}: {prompt}"
``````

### Multiple Bindings

``````python
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

@mint.experiment()
def process(
    data: str,
    llm_config: Annotated[LLMConfig, Bind("llm")],
    db_config: Annotated[DatabaseConfig, Bind("db")]
) -> str:
    return f"Processing with {llm_config.model} on {db_config.host}"
``````

### Instance-Level Bindings

Set bindings at Spearmint initialization:

``````python
mint = Spearmint(
    configs=configs,
    bindings={
        LLMConfig: "llm",
        DatabaseConfig: "db"
    }
)

@mint.experiment()
def process(data: str, config: LLMConfig) -> str:
    # LLMConfig automatically bound to "llm" path
    return f"Processing with {config.model}"
``````

---

## Configuration Access

### Dictionary Access

``````python
@mint.experiment()
def process(text: str, config: Config) -> str:
    model = config['model']
    temp = config['temperature']
    return f"{model} at {temp}"
``````

### Nested Access

``````python
configs = [{
    "llm": {
        "model": "gpt-4",
        "params": {
            "temperature": 0.7
        }
    }
}]

@mint.experiment()
def process(text: str, config: Config) -> str:
    model = config['llm']['model']
    temp = config['llm']['params']['temperature']
    return f"{model} at {temp}"
``````

### Default Values

``````python
@mint.experiment()
def process(text: str, config: Config) -> str:
    # Use .get() for defaults
    model = config.get('model', 'gpt-3.5-turbo')
    temp = config.get('temperature', 0.5)
    return f"{model} at {temp}"
``````

---

## Configuration IDs

Each configuration gets a unique ID for tracking.

### Auto-Generated IDs

By default, IDs are SHA256 hashes:

``````python
import hashlib
import json

config = {"model": "gpt-4", "temperature": 0.7}
config_str = json.dumps(config, sort_keys=True)
config_id = hashlib.sha256(config_str.encode()).hexdigest()[:16]
``````

### Custom IDs

Override with `__config_id__`:

``````python
configs = [
    {
        "model": "gpt-4",
        "__config_id__": "production-model"
    },
    {
        "model": "gpt-3.5-turbo",
        "__config_id__": "fallback-model"
    }
]
``````

**Benefits:**
- Readable IDs in logs and traces
- Stable IDs across runs
- Easy to reference in analysis

---

## Best Practices

### 1. Use Type-Safe Bindings

``````python
# ✅ Good - type-safe, IDE support
@mint.experiment()
def process(text: str, config: Annotated[LLMConfig, Bind("")]) -> str:
    return f"{config.model}: {text}"

# ❌ Avoid - no type safety
@mint.experiment()
def process(text: str, config: dict) -> str:
    return f"{config['model']}: {text}"
``````

### 2. Keep Configs Flat When Possible

``````python
# ✅ Good - simple and clear
config = {
    "model": "gpt-4",
    "temperature": 0.7
}

# ❌ Avoid unless necessary - adds complexity
config = {
    "llm": {
        "settings": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
}
``````

### 3. Use DynamicValue for Parameter Sweeps

``````python
# ✅ Good - generates all combinations
configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5"]),
    "temperature": DynamicValue([0.0, 0.5])
}]

# ❌ Tedious - manual config creation
configs = [
    {"model": "gpt-4", "temperature": 0.0},
    {"model": "gpt-4", "temperature": 0.5},
    {"model": "gpt-3.5", "temperature": 0.0},
    {"model": "gpt-3.5", "temperature": 0.5},
]
``````

### 4. Version Your Config Files

``````yaml
# config.yaml
version: "1.0"
model: gpt-4
temperature: 0.7
``````

Track version in config for reproducibility.

---

## Advanced Patterns

### Environment-Specific Configs

``````python
import os

environment = os.getenv("ENV", "development")
config_file = f"configs/{environment}.yaml"

mint = Spearmint(configs=[config_file])
``````

### Config Validation

``````python
from pydantic import BaseModel, Field, field_validator

class ValidatedConfig(BaseModel):
    model: str = Field(pattern="^gpt-")
    temperature: float = Field(ge=0.0, le=2.0)
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        allowed = ["gpt-4", "gpt-3.5-turbo"]
        if v not in allowed:
            raise ValueError(f"Model must be one of {allowed}")
        return v
``````

### Config Inheritance

``````python
base_config = {
    "temperature": 0.7,
    "max_tokens": 1000
}

configs = [
    {**base_config, "model": "gpt-4"},
    {**base_config, "model": "gpt-3.5-turbo"},
]
``````

---

## See Also

- [API Reference](api.md) - Complete configuration API
- [Strategies](strategies.md) - Execution strategies for configs
- [Architecture](../explanation/architecture.md) - How config system works internally
