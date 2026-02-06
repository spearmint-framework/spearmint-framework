# Spearmint Class Reference

The main class for managing experiments and configurations.

## Class Definition

``````python
class Spearmint:
    def __init__(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: Sequence[dict[str, Any] | Config | str | Path] | None = None,
    ) -> None:
        ...
``````

## Constructor Parameters

### `branch_strategy`
**Type:** `Callable[..., tuple[Config, list[Config]]] | None`  
**Default:** `None`

Optional callable that determines which configuration is primary and which are variants.

**Signature:**
``````python
def strategy(*args, **kwargs) -> tuple[Config, list[Config]]:
    """
    Returns:
        tuple: (primary_config, list_of_variant_configs)
    """
``````

**Example:**
``````python
def my_strategy(*args, **kwargs):
    configs = get_all_configs()
    return configs[0], configs[1:]  # First is primary

mint = Spearmint(branch_strategy=my_strategy, configs=[...])
``````

### `configs`
**Type:** `Sequence[dict | Config | str | Path] | None`  
**Default:** `None`

Configuration sources. Accepts:
- **Dictionaries:** `{"model": "gpt-4", "temperature": 0.7}`
- **Config objects:** Pre-parsed `Config` instances
- **File paths:** `"config.yaml"` or `Path("config.yaml")`
- **Directory paths:** `"configs/"` loads all YAML files

**Examples:**
``````python
# Dictionary configs
mint = Spearmint(configs=[{"model": "gpt-4"}])

# YAML file
mint = Spearmint(configs=["config.yaml"])

# Directory of configs
mint = Spearmint(configs=["configs/"])

# Mixed
mint = Spearmint(configs=[
    {"model": "gpt-4"},
    "other_config.yaml",
    Config(id="custom", data={"key": "value"})
])
``````

## Instance Methods

### `experiment()`

Decorator for wrapping functions with experiment execution.

**Signature:**
``````python
def experiment(
    self,
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
    configs: Sequence[dict[str, Any] | Config | str | Path] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    ...
``````

**Parameters:**
- `branch_strategy`: Override instance-level strategy
- `configs`: Override instance-level configs

**Returns:** Decorator function

**Usage:**
``````python
mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return f"{config['model']}: {prompt}"

# Override configs per function
@mint.experiment(configs=[{"model": "gpt-3.5-turbo"}])
def other_function(config: Config) -> str:
    return config["model"]
``````

**Behavior:**
1. Automatically detects sync vs async functions
2. Injects `config: Config` parameter
3. Registers function in global registry
4. Returns wrapped function that executes with configuration

**Async Support:**
``````python
@mint.experiment()
async def async_generate(prompt: str, config: Config) -> str:
    await asyncio.sleep(0.1)
    return f"{config['model']}: {prompt}"
``````

## Static Methods

### `run()`

Context manager for explicit sync experiment execution.

**Signature:**
``````python
@staticmethod
@contextmanager
def run(
    func: Callable[..., Any],
    await_variants: bool = False
) -> ExperimentRunner:
    ...
``````

**Parameters:**
- `func`: Experiment function to run
- `await_variants`: Wait for variant executions to complete

**Returns:** Context manager yielding `ExperimentRunner`

**Usage:**
``````python
@mint.experiment()
def my_function(prompt: str, config: Config) -> str:
    return f"Result: {prompt}"

with Spearmint.run(my_function) as runner:
    results = runner("test prompt")
    print(results.main_result.result)
    print(results.main_result.experiment_case.config.id)
``````

**Why use `run()`?**
- Access detailed results and metadata
- Better control for testing
- Batch processing workflows
- Custom result handling

### `arun()`

Context manager for explicit async experiment execution.

**Signature:**
``````python
@staticmethod
@asynccontextmanager
async def arun(
    func: Callable[..., Any],
    await_variants: bool = False
) -> ExperimentRunner:
    ...
``````

**Parameters:**
- `func`: Async experiment function to run
- `await_variants`: Wait for variant executions to complete

**Returns:** Async context manager yielding `ExperimentRunner`

**Usage:**
``````python
@mint.experiment()
async def async_function(prompt: str, config: Config) -> str:
    await some_async_call()
    return f"Result: {prompt}"

async def main():
    async with Spearmint.arun(async_function) as runner:
        results = await runner("test prompt")
        print(results.main_result.result)

asyncio.run(main())
``````

## Complete Example

``````python
from spearmint import Spearmint, Config
from pathlib import Path

# Initialize with configs from multiple sources
mint = Spearmint(
    configs=[
        {"model": "gpt-4", "temperature": 0.7},
        "config.yaml",
        Path("configs/")
    ]
)

# Decorate functions
@mint.experiment()
def process_text(text: str, config: Config) -> dict:
    return {
        "model": config["model"],
        "temperature": config.get("temperature", 1.0),
        "result": f"Processed: {text}"
    }

# Direct call (uses first config)
result = process_text("Hello world")

# Explicit execution with full control
with Spearmint.run(process_text) as runner:
    results = runner("Hello world")
    
    # Access primary result
    print(results.main_result.result)
    
    # Access config details
    config_id = results.main_result.experiment_case.config.id
    print(f"Config ID: {config_id}")
    
    # Check variant results (if any)
    for variant in results.variant_results:
        print(f"Variant: {variant.experiment_case.config.id}")
``````

## See Also

- [Experiment Decorator Reference](experiment.md)
- [Runner APIs](runner.md)
- [Config Object](config.md)
- [Branch Strategies](../strategies.md)
