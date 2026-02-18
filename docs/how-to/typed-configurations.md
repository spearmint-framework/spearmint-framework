# Typed Configurations with Pydantic

Use Pydantic models for type-safe, validated configuration management in your experiments.

## Problem

Plain dictionaries for configuration lack:

- **Type safety**: No autocomplete or type checking
- **Validation**: No automatic validation of values
- **Documentation**: No clear structure for configuration options
- **Defaults**: Manual handling of optional parameters

## Solution

Use Pydantic models as configuration types. Spearmint automatically validates and injects them into your experiment functions.

## Basic Usage

Define a Pydantic model and use it as a parameter type:

``````python
from pydantic import BaseModel
from spearmint import Spearmint

class ModelConfig(BaseModel):
    model_name: str
    temperature: float
    max_tokens: int = 100  # Default value

mint = Spearmint(
    configs=[
        {"model_name": "gpt-4", "temperature": 0.5},
        {"model_name": "gpt-3.5", "temperature": 0.9, "max_tokens": 50},
    ]
)

@mint.experiment()
def generate(prompt: str, model_config: ModelConfig) -> str:
    # model_config is automatically validated and typed
    return f"Using {model_config.model_name} with temp {model_config.temperature}"

if __name__ == "__main__":
    with Spearmint.run(generate, await_variants=True) as runner:
        result = runner("Test prompt")
        print(result.main_result.result)
``````

## Benefits

### Type Safety

Get autocomplete and type checking in your IDE:

``````python
@mint.experiment()
def generate(prompt: str, model_config: ModelConfig) -> str:
    # IDE knows model_config.model_name is a string
    # IDE knows model_config.temperature is a float
    return model_config.model_name.upper()  # Autocomplete works!
``````

### Automatic Validation

Pydantic validates configuration automatically:

``````python
class ModelConfig(BaseModel):
    model_name: str
    temperature: float
    max_tokens: int = 100
    
    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

# This will raise a validation error:
# mint = Spearmint(configs=[{"model_name": "gpt-4", "temperature": 3.0}])
``````

### Default Values

Use Pydantic's default values:

``````python
class ModelConfig(BaseModel):
    model_name: str
    temperature: float = 0.7  # Default
    max_tokens: int = 100     # Default

# Only required fields needed:
mint = Spearmint(configs=[{"model_name": "gpt-4"}])
``````

## Nested Configuration with Binding

For complex configurations, use `Bind` to extract nested paths:

``````python
from typing import Annotated
from pydantic import BaseModel
from spearmint import Spearmint
from spearmint.configuration import Bind

class LLMConfig(BaseModel):
    model: str
    temperature: float

class DatabaseConfig(BaseModel):
    host: str
    port: int

# Configuration with nested structure
config = {
    "llm": {
        "model": "gpt-4",
        "temperature": 0.5
    },
    "database": {
        "host": "localhost",
        "port": 5432
    }
}

mint = Spearmint(configs=[config])

@mint.experiment()
def process(
    llm_config: Annotated[LLMConfig, Bind("llm")],
    db_config: Annotated[DatabaseConfig, Bind("database")]
) -> str:
    return f"Using {llm_config.model} and DB at {db_config.host}:{db_config.port}"
``````

## Advanced Validation

### Field Constraints

Use Pydantic's built-in constraints:

``````python
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    model_name: str = Field(..., min_length=1)
    temperature: float = Field(..., ge=0.0, le=2.0)
    max_tokens: int = Field(default=100, gt=0, le=4000)
``````

### Custom Validators

Add custom validation logic:

``````python
from pydantic import BaseModel, validator

class ModelConfig(BaseModel):
    model_name: str
    temperature: float
    
    @validator("model_name")
    def validate_model(cls, v):
        allowed = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        if v not in allowed:
            raise ValueError(f"Model must be one of {allowed}")
        return v
``````

## YAML with Pydantic

Combine typed configs with YAML files:

``````yaml
# config.yaml
model_name: gpt-4
temperature: 0.7
max_tokens: 150
``````

``````python
mint = Spearmint(configs=["config.yaml"])

@mint.experiment()
def generate(model_config: ModelConfig) -> str:
    # Config is loaded from YAML and validated
    return f"Using {model_config.model_name}"
``````

## Complete Example

Here's a full example with validation and defaults:

``````python
from typing import Annotated
from pydantic import BaseModel, Field, validator
from spearmint import Spearmint
from spearmint.configuration import Bind

class ModelConfig(BaseModel):
    """Configuration for LLM model."""
    model_name: str = Field(..., description="Name of the model to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(100, gt=0, le=4000, description="Maximum tokens to generate")
    
    @validator("model_name")
    def validate_model(cls, v):
        allowed = ["gpt-4", "gpt-3.5-turbo"]
        if v not in allowed:
            raise ValueError(f"Model must be one of {allowed}")
        return v

mint = Spearmint(
    configs=[
        {"model_name": "gpt-4", "temperature": 0.5},
        {"model_name": "gpt-3.5-turbo", "temperature": 0.9, "max_tokens": 50},
    ]
)

@mint.experiment()
def generate(prompt: str, model_config: ModelConfig) -> str:
    """Generate text using the configured model."""
    return (
        f"Prompt: {prompt}, "
        f"Model: {model_config.model_name}, "
        f"Temp: {model_config.temperature}, "
        f"MaxTokens: {model_config.max_tokens}"
    )

if __name__ == "__main__":
    with Spearmint.run(generate, await_variants=True) as runner:
        result = runner("Test prompt")
        print(f"Main: {result.main_result.result}")
        for variant in result.variant_results:
            print(f"Variant: {variant.result}")
``````

## See Also

- [Configuration Basics](../tutorials/configuration-basics.md) - Learn configuration fundamentals
- [Config Binding](../reference/api/config-binding.md) - Details on `Bind` annotation
- [Cookbook: Typed Config Example](https://github.com/spearmint-framework/spearmint-framework/blob/main/cookbook/configuration/typed_config.py)
