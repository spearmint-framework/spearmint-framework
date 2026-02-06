# Core Concepts

Understanding Spearmint's core concepts will help you use it effectively.

## Overview

Spearmint automates the process of testing multiple configurations of your code. It handles:
- Configuration management and injection
- Experiment execution strategies
- Result tracking and comparison

## The Three Pillars

### 1. Configurations

A **configuration** is a set of parameters you want to test. Configurations can be:

- **Python dictionaries**
  ```python
  {"model": "gpt-4", "temperature": 0.7}
  ```

- **YAML files**
  ```yaml
  # config.yaml
  model: gpt-4
  temperature: 0.7
  ```

- **Pydantic models**
  ```python
  from pydantic import BaseModel
  
  class LLMConfig(BaseModel):
      model: str
      temperature: float
  ```

Configurations are automatically injected into your experiment functions.

### 2. Experiments

An **experiment** is a function decorated with `@experiment()` that accepts a `config` parameter:

```python
@mint.experiment()
def my_function(input_data: str, config: dict) -> str:
    # config is automatically injected
    return process(input_data, config['model'])
```

Key characteristics:
- Can be sync or async
- Always receives a `config` parameter
- Returns results like a normal function
- Automatically tracked and logged

### 3. Strategies

**Strategies** control *how* your configurations are executed. While the current implementation uses a default strategy, the concept is important for understanding Spearmint's design:

- **Single Config**: Runs one configuration (default behavior)
- **Shadow**: Primary config runs in foreground, others in background
- **Multi-Branch**: All configs run in parallel, all results returned
- **Round Robin**: Cycles through configs on each call

> **Note**: Advanced strategy support is on the roadmap. Currently, Spearmint uses a single-config execution model.

## Configuration Lifecycle

Understanding how configurations flow through Spearmint:

```
1. Define configs → 2. Parse/expand → 3. Inject → 4. Execute → 5. Track results
```

### 1. Define Configurations

Start by defining your configurations:

```python
mint = Spearmint(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"}
])
```

### 2. Parse and Expand

Spearmint processes your configurations:
- Loads YAML files if needed
- Expands `DynamicValue` entries into multiple configs
- Validates structure

```python
from spearmint.configuration import DynamicValue

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5])
}]
# Expands to 4 configurations (2 models × 2 temperatures)
```

### 3. Inject Configuration

When your function runs, Spearmint injects the appropriate config:

```python
@mint.experiment()
def process(text: str, config: dict) -> str:
    # config is injected here
    return call_api(config['model'], text)
```

### 4. Execute

Spearmint manages execution:
- Determines which config(s) to use
- Handles sync/async appropriately
- Manages context and lifecycle

### 5. Track Results

Results are automatically tracked:
- Execution time
- Success/failure status
- Output values
- Configuration used

## Dynamic Value Expansion

`DynamicValue` allows you to generate multiple configurations from iterables:

```python
from spearmint.configuration import DynamicValue

def custom_generator():
    for i in range(3):
        yield i * 0.5

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue(custom_generator()),
    "max_tokens": DynamicValue(range(100, 301, 100))
}]
# Creates 2 × 3 × 3 = 18 configurations
```

Any iterable works:
- Lists: `["a", "b", "c"]`
- Ranges: `range(0, 10)`
- Generators: `(x for x in my_list)`
- Custom iterables

## Configuration Binding

Bind configurations to typed Pydantic models for type safety:

```python
from pydantic import BaseModel

class ModelConfig(BaseModel):
    model: str
    temperature: float

# Bind to root level
@mint.experiment(bindings={ModelConfig: ""})
def generate(prompt: str, config: ModelConfig) -> str:
    return f"{config.model}: {prompt}"
```

### Nested Binding

Access nested configuration values with dot notation:

```python
configs = [{
    "llm": {
        "model_config": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
}]

@mint.experiment(bindings={ModelConfig: "llm.model_config"})
def generate(prompt: str, config: ModelConfig) -> str:
    return f"{config.model}: {prompt}"
```

## Execution Modes

### Decorator Mode (Implicit)

Most common for production code:

```python
@mint.experiment()
def my_function(input: str, config: dict) -> str:
    return process(input, config)

# Call like a normal function
result = my_function("input")
```

### Runner Mode (Explicit)

Better for batch processing and detailed result access:

```python
@mint.experiment()
def my_function(input: str, config: dict) -> str:
    return process(input, config)

# Explicitly manage execution
with Spearmint.run(my_function) as runner:
    results = runner("input")
    print(results.main_result.result)
    print(results.variant_results)
```

### Async Support

Spearmint automatically handles async functions:

```python
@mint.experiment()
async def async_function(input: str, config: dict) -> str:
    await asyncio.sleep(0.1)
    return process(input, config)

# Use with await
result = await async_function("input")

# Or with async runner
async with Spearmint.arun(async_function) as runner:
    results = await runner("input")
```

## Result Objects

When using runner mode, you get structured results:

```python
class FunctionResult:
    result: Any              # The function's return value
    experiment_case: ExperimentCase  # Configuration used

class ExperimentCaseResults:
    main_result: FunctionResult      # Primary configuration result
    variant_results: list[FunctionResult]  # Other configurations
```

Access results:

```python
with Spearmint.run(my_function) as runner:
    results = runner("input")
    
    # Main result (first config)
    main_output = results.main_result.result
    
    # Variant results (other configs)
    for variant in results.variant_results:
        print(variant.result)
```

## Configuration IDs

Each configuration gets a unique ID for tracking:

```python
configs = [
    {"model": "gpt-4"},  # config_id auto-generated
    {"config_id": "custom-id", "model": "gpt-3.5"}  # explicit ID
]
```

Configuration IDs are used for:
- Result tracking
- MLflow logging
- Debugging and analysis

## Best Practices

### 1. Start Simple

Begin with basic dictionary configs:

```python
mint = Spearmint(configs=[{"model": "gpt-4"}])
```

Add complexity as needed.

### 2. Use Type Safety When Helpful

For complex configs, use Pydantic models:

```python
class ComplexConfig(BaseModel):
    model: str
    temperature: float
    retry_count: int = 3
    timeout: float = 30.0

@mint.experiment(bindings={ComplexConfig: ""})
def process(input: str, config: ComplexConfig) -> str:
    # IDE autocomplete and type checking
    return call_with_retries(config.model, config.retry_count)
```

### 3. Keep Functions Pure

Experiment functions should be deterministic when possible:

```python
# Good: Pure function
@mint.experiment()
def process(input: str, config: dict) -> str:
    return transform(input, config['param'])

# Avoid: Hidden side effects
@mint.experiment()
def process(input: str, config: dict) -> str:
    save_to_database(input)  # Side effect
    return transform(input, config['param'])
```

### 4. Use Descriptive Config IDs

For debugging and analysis:

```python
configs = [
    {"config_id": "prod-gpt4-low-temp", "model": "gpt-4", "temperature": 0.0},
    {"config_id": "prod-gpt4-high-temp", "model": "gpt-4", "temperature": 0.9},
]
```

## Common Patterns

### Pattern: Gradual Rollout

Test new configurations in production:

```python
mint = Spearmint(configs=[
    {"version": "stable"},    # Primary
    {"version": "canary"},    # Shadow test
])

@mint.experiment()
def api_handler(request: dict, config: dict) -> dict:
    return process_with_version(request, config['version'])
```

### Pattern: Parameter Tuning

Find optimal parameters:

```python
from spearmint.configuration import DynamicValue

mint = Spearmint(configs=[{
    "temperature": DynamicValue([i/10 for i in range(0, 11)]),
    "top_p": DynamicValue([0.9, 0.95, 1.0])
}])
# Creates 33 configurations to test
```

### Pattern: Model Comparison

Compare different models or algorithms:

```python
mint = Spearmint(configs=[
    {"model": "gpt-4", "cost_per_token": 0.00003},
    {"model": "gpt-3.5-turbo", "cost_per_token": 0.000002},
    {"model": "claude-3", "cost_per_token": 0.000015},
])
```

## Next Steps

- **[How-To Guides](../how-to/configurations.md)** - Practical techniques
- **[API Reference](../reference/api/spearmint.md)** - Complete API docs
- **[Architecture](../explanation/architecture.md)** - How Spearmint works
- **[Cookbook](../../cookbook/README.md)** - More examples
