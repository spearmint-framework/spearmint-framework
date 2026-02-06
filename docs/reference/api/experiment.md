# Experiment Decorator

The `@experiment` decorator transforms regular functions into experiment-aware functions that automatically handle configuration injection, variant execution, and result tracking.

## Usage

### As a Method Decorator

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def my_function(prompt: str, config: Config) -> str:
    return f"Using {config['model']}: {prompt}"
``````

### As a Standalone Decorator

``````python
from spearmint import experiment, Config

@experiment(configs=[{"model": "gpt-4"}])
def my_function(prompt: str, config: Config) -> str:
    return f"Using {config['model']}: {prompt}"
``````

## Signature

### Method Signature

``````python
Spearmint.experiment(
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
    configs: Sequence[dict | Config | str | Path] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]
``````

### Standalone Function Signature

``````python
experiment(
    configs: Sequence[dict | Config | str | Path],
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]
``````

## Parameters

### `branch_strategy`
**Type:** `Callable[..., tuple[Config, list[Config]]] | None`  
**Default:** `None` (uses instance strategy or default)

Optional callable that determines how configurations are split between primary and variant branches.

**Signature:**
``````python
def strategy(configs: list[Config], ctx: RuntimeContext) -> tuple[Config, list[Config]]:
    """
    Args:
        configs: List of all configurations
        ctx: Runtime context information
    
    Returns:
        tuple: (primary_config, variant_configs_list)
    """
``````

**Example:**
``````python
def shadow_strategy(configs: list[Config], ctx: RuntimeContext) -> tuple[Config, list[Config]]:
    # First config is primary, rest are shadows
    return configs[0], configs[1:]

@mint.experiment(branch_strategy=shadow_strategy)
def my_function(config: Config) -> str:
    return config['model']
``````

### `configs`
**Type:** `Sequence[dict | Config | str | Path] | None`  
**Default:** `None` (uses instance configs)

Configuration sources to use for this specific experiment. Overrides the Spearmint instance's configurations.

**Accepts:**
- **Dictionaries:** `{"model": "gpt-4", "temperature": 0.7}`
- **Config objects:** Pre-parsed `Config` instances
- **File paths:** `"config.yaml"` or `Path("config.yaml")`
- **Directory paths:** Loads all YAML files from directory

**Example:**
``````python
# Override instance configs for specific function
@mint.experiment(configs=[
    {"model": "gpt-4o"},
    {"model": "gpt-4o-mini"}
])
def specific_function(config: Config) -> str:
    return config['model']
``````

## Behavior

### Synchronous Functions

For synchronous functions, the decorator:
1. Wraps the function with experiment tracking
2. Injects configuration parameters automatically
3. Returns the result from the primary configuration
4. Executes variant configurations in background threads (unless `await_variants=True`)

``````python
@mint.experiment()
def sync_function(prompt: str, config: Config) -> str:
    return f"Result: {prompt}"

# Call like a normal function
result = sync_function("test")  # Returns primary result immediately
``````

### Asynchronous Functions

For async functions, the decorator:
1. Preserves async behavior
2. Injects configuration parameters
3. Returns the result from the primary configuration
4. Executes variant configurations as background tasks

``````python
@mint.experiment()
async def async_function(prompt: str, config: Config) -> str:
    await asyncio.sleep(0.1)
    return f"Result: {prompt}"

# Call with await
result = await async_function("test")
``````

## Configuration Injection

The decorator automatically injects configuration values into function parameters:

### Dict-like Config Parameter

``````python
@mint.experiment()
def my_function(prompt: str, config: Config) -> str:
    # Access config as dictionary
    model = config["model"]
    temp = config["temperature"]
    return f"{model} at {temp}"
``````

### Typed Configuration with Binding

``````python
from pydantic import BaseModel

class ModelConfig(BaseModel):
    model: str
    temperature: float

mint = Spearmint(configs=[{"model": "gpt-4", "temperature": 0.7}])

@mint.experiment()
def my_function(prompt: str, config: Annotated[ModelConfig, Bind("")]) -> str:
    # config is now a typed ModelConfig object
    return f"{config.model} at {config.temperature}"
``````

## Return Values

### Direct Call (Default Behavior)

When called directly, the decorated function returns only the primary result:

``````python
@mint.experiment()
def my_function(config: Config) -> str:
    return config['model']

result = my_function()  # Returns: "gpt-4" (primary result only)
``````

### Using Run Context Manager

To access all results including variants:

``````python
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner()
    print(results.main_result.result)  # Primary result
    for variant in results.variant_results:
        print(variant.result)  # Variant results
``````

## Integration with MLflow

Decorated functions automatically create MLflow traces:

``````python
import mlflow

@mint.experiment()
def tracked_function(prompt: str, config: Config) -> str:
    return f"Result for {prompt}"

# Function execution is automatically logged
result = tracked_function("test prompt")

# View traces
traces = mlflow.search_traces()
for trace in traces:
    print(trace.info.request_id)
``````

## Error Handling

### Function Exceptions

Exceptions in the primary function are propagated to the caller:

``````python
@mint.experiment()
def failing_function(config: Config) -> str:
    raise ValueError("Something went wrong")

try:
    result = failing_function()
except ValueError as e:
    print(f"Caught: {e}")
``````

### Variant Exceptions

Exceptions in variant configurations are logged but don't affect the primary result:

``````python
mint = Spearmint(configs=[
    {"model": "working"},
    {"model": "failing"}
])

@mint.experiment(branch_strategy=lambda cfgs, ctx: (cfgs[0], cfgs[1:]))
def function_with_variants(config: Config) -> str:
    if config['model'] == "failing":
        raise ValueError("Variant failed")
    return "success"

result = function_with_variants()  # Returns "success" from primary
# Variant failure is logged, not raised
``````

## See Also

- [Spearmint Class](spearmint.md) - Main framework class
- [Runner APIs](runner.md) - Direct experiment execution
- [Config Object](config.md) - Configuration structure
- [Config Binding](config-binding.md) - Type-safe configuration binding
- [Results](results.md) - Result structure details
