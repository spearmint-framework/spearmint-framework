# Config Binding

Type-safe configuration injection using Pydantic models and the `Bind` class.

## Overview

Config binding allows you to:
- Use strongly-typed Pydantic models instead of `Config` dicts
- Get full IDE autocomplete and type checking
- Bind nested configuration paths to function parameters
- Validate configuration at runtime with Pydantic

## The Bind Class

``````python
class Bind:
    """Indicates binding of configuration models to function parameters."""
    
    def __init__(self, path: str) -> None:
        """
        Args:
            path: Dot-notation path to configuration subset.
                  Empty string ("") binds to root.
        """
        self.path = path
``````

## Basic Usage

### Root Binding

Bind entire configuration to a Pydantic model:

``````python
from typing import Annotated
from pydantic import BaseModel
from spearmint import Spearmint
from spearmint.configuration import Bind

class ModelConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int = 1000

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7}
])

@mint.experiment()
def generate(
    prompt: str,
    config: Annotated[ModelConfig, Bind("")]
) -> str:
    # config is now ModelConfig with full type safety
    return f"{config.model}: {prompt}"

# IDE provides autocomplete for config.model, config.temperature, etc.
``````

### Nested Path Binding

Bind to a specific path in the configuration:

``````python
from typing import Annotated
from pydantic import BaseModel
from spearmint import Spearmint
from spearmint.configuration import Bind

class LLMParams(BaseModel):
    model: str
    temperature: float

mint = Spearmint(configs=[{
    "service": {
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7
        },
        "timeout": 30
    }
}])

@mint.experiment()
def generate(
    prompt: str,
    params: Annotated[LLMParams, Bind("service.llm")]
) -> str:
    # params bound to config["service"]["llm"]
    return f"{params.model}: {prompt}"
``````

## Path Syntax

The `Bind` path uses dot notation to navigate configuration structure:

``````python
# Configuration structure
config = {
    "level1": {
        "level2": {
            "level3": {
                "value": 42
            }
        }
    }
}

# Bind to nested value
Bind("level1.level2.level3")  # Binds to {"value": 42}
``````

## Multiple Bindings

Bind multiple parameters to different configuration paths:

``````python
from typing import Annotated
from pydantic import BaseModel
from spearmint.configuration import Bind

class ModelConfig(BaseModel):
    model: str
    temperature: float

class RetryConfig(BaseModel):
    max_retries: int
    timeout: float

mint = Spearmint(configs=[{
    "llm": {
        "model": "gpt-4",
        "temperature": 0.7
    },
    "retry": {
        "max_retries": 3,
        "timeout": 30.0
    }
}])

@mint.experiment()
def robust_generate(
    prompt: str,
    model_cfg: Annotated[ModelConfig, Bind("llm")],
    retry_cfg: Annotated[RetryConfig, Bind("retry")]
) -> str:
    # model_cfg bound to config["llm"]
    # retry_cfg bound to config["retry"]
    return generate_with_retry(prompt, model_cfg, retry_cfg)
``````

## Validation

Pydantic validates bound configurations at runtime:

``````python
from pydantic import BaseModel, Field
from spearmint.configuration import Bind
from typing import Annotated

class ValidatedConfig(BaseModel):
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(gt=0, le=4096)

mint = Spearmint(configs=[
    {"temperature": 0.7, "max_tokens": 1000}  # Valid
])

@mint.experiment()
def validated_func(
    config: Annotated[ValidatedConfig, Bind("")]
) -> str:
    return f"temp={config.temperature}"

# This config would raise ValidationError
# mint = Spearmint(configs=[
#     {"temperature": 3.0, "max_tokens": 1000}  # Invalid: temp > 2.0
# ])
``````

## With DynamicValue

Binding works with DynamicValue-generated configs:

``````python
from pydantic import BaseModel
from spearmint.configuration import Bind, DynamicValue
from typing import Annotated

class ModelConfig(BaseModel):
    model: str
    temperature: float

mint = Spearmint(configs=[{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.7])
}])

@mint.experiment()
def compare_models(
    prompt: str,
    config: Annotated[ModelConfig, Bind("")]
) -> str:
    # Each of the 4 generated configs is validated against ModelConfig
    return f"{config.model}: {prompt}"
``````

## Complex Example

``````python
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from spearmint import Spearmint
from spearmint.configuration import Bind

class ModelParams(BaseModel):
    model: Literal["gpt-4", "gpt-3.5-turbo", "gpt-4o"]
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(gt=0, le=4096)
    top_p: float = Field(ge=0.0, le=1.0, default=1.0)

class RetryPolicy(BaseModel):
    max_retries: int = Field(ge=0, le=10)
    initial_delay: float = Field(gt=0.0)
    backoff_factor: float = Field(ge=1.0)

class ServiceConfig(BaseModel):
    timeout_seconds: int = Field(gt=0, le=300)
    api_key_name: str

mint = Spearmint(configs=[{
    "llm": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.95
    },
    "retry": {
        "max_retries": 3,
        "initial_delay": 1.0,
        "backoff_factor": 2.0
    },
    "service": {
        "timeout_seconds": 60,
        "api_key_name": "OPENAI_API_KEY"
    }
}])

@mint.experiment()
def production_generate(
    prompt: str,
    model: Annotated[ModelParams, Bind("llm")],
    retry: Annotated[RetryPolicy, Bind("retry")],
    service: Annotated[ServiceConfig, Bind("service")]
) -> str:
    # All parameters are fully typed and validated
    return call_llm_with_retry(prompt, model, retry, service)
``````

## Comparison: Config vs Binding

### Using Config Dict

``````python
from spearmint import Config

@mint.experiment()
def without_binding(prompt: str, config: Config) -> str:
    # Dict-like access, no type checking
    model = config["model"]  # Any type
    temp = config["temperature"]  # Any type
    
    # IDE can't help with autocomplete
    # Typos not caught: config["temperture"]
    
    return f"{model}: {prompt}"
``````

### Using Binding

``````python
from typing import Annotated
from pydantic import BaseModel
from spearmint.configuration import Bind

class ModelConfig(BaseModel):
    model: str
    temperature: float

@mint.experiment()
def with_binding(
    prompt: str,
    config: Annotated[ModelConfig, Bind("")]
) -> str:
    # Typed access with IDE support
    model = config.model  # str
    temp = config.temperature  # float
    
    # IDE provides autocomplete
    # Typos caught by type checker and IDE
    
    return f"{model}: {prompt}"
``````

## Benefits

1. **Type Safety**: Catch configuration errors at design time
2. **IDE Support**: Autocomplete and inline documentation
3. **Validation**: Pydantic validates configuration structure and values
4. **Refactoring**: Rename safely with IDE refactoring tools
5. **Documentation**: Pydantic models serve as configuration documentation

## Limitations

### Must Use Annotated

``````python
# ❌ This won't work
@mint.experiment()
def wrong(prompt: str, config: Bind("llm")) -> str:
    pass

# ✅ Must use Annotated
@mint.experiment()
def correct(
    prompt: str,
    config: Annotated[ModelConfig, Bind("llm")]
) -> str:
    pass
``````

### Path Must Exist

``````python
class ModelConfig(BaseModel):
    model: str

# Config without the expected path
mint = Spearmint(configs=[{"temperature": 0.7}])

@mint.experiment()
def will_fail(
    config: Annotated[ModelConfig, Bind("llm.model")]
) -> str:
    pass

# Raises error: path "llm.model" not found in config
``````

## See Also

- [Config Object](config.md) - Dictionary-based configuration
- [Typed Configurations How-To](../../how-to/typed-configurations.md) - Practical guide
- [Configuration Design](../../explanation/configuration-design.md) - Design philosophy
