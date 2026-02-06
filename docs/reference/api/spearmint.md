# Spearmint Class API Reference

The `Spearmint` class is the main entry point for creating experiments.

## Class: `Spearmint`

```python
class Spearmint:
    def __init__(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: Sequence[dict[str, Any] | Config | str | Path] | None = None,
    ) -> None
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `branch_strategy` | `Callable` or `None` | `None` | Strategy for selecting main and variant configurations. Reserved for future use. |
| `configs` | `Sequence` or `None` | `None` | List of configurations to use for experiments. Can be dicts, Config objects, file paths, or directory paths. |

### Configuration Input Types

The `configs` parameter accepts multiple formats:

**Python dictionaries:**
```python
Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7}
])
```

**File paths (YAML):**
```python
Spearmint(configs=["config.yaml"])
```

**Directory paths (loads all YAML files):**
```python
Spearmint(configs=["configs/"])
```

**Config objects:**
```python
from spearmint.configuration import Config

Spearmint(configs=[Config({"model": "gpt-4"})])
```

**Mixed formats:**
```python
Spearmint(configs=[
    {"model": "gpt-4"},
    "config.yaml",
    "configs/"
])
```

## Instance Methods

### `experiment()`

Decorator for wrapping functions with experiment execution.

```python
def experiment(
    self,
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
    configs: Sequence[dict[str, Any] | Config | str | Path] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `branch_strategy` | `Callable` or `None` | `None` | Override the instance-level strategy. Reserved for future use. |
| `configs` | `Sequence` or `None` | `None` | Override the instance-level configurations. |

#### Returns

A decorator function that wraps the target function.

#### Example

```python
mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def generate_text(prompt: str, config: dict) -> str:
    return f"{config['model']}: {prompt}"

result = generate_text("Hello")
```

#### With Config Overrides

```python
mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment(configs=[{"model": "gpt-3.5-turbo"}])
def generate_text(prompt: str, config: dict) -> str:
    return f"{config['model']}: {prompt}"
```

## Static Methods

### `run()`

Context manager for explicit synchronous experiment execution.

```python
@staticmethod
@contextmanager
def run(
    func: Callable[..., Any],
    await_variants: bool = False
) -> Iterator[ExperimentRunner]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `Callable` | (required) | The experiment function to run. Must be decorated with `@experiment()`. |
| `await_variants` | `bool` | `False` | Whether to wait for variant configurations to complete. |

#### Returns

A context manager that yields an `ExperimentRunner` instance.

#### Example

```python
@mint.experiment()
def process(input: str, config: dict) -> str:
    return f"{config['model']}: {input}"

with Spearmint.run(process) as runner:
    results = runner("test input")
    print(results.main_result.result)
```

### `arun()`

Context manager for explicit asynchronous experiment execution.

```python
@staticmethod
@asynccontextmanager
async def arun(
    func: Callable[..., Any],
    await_variants: bool = False
) -> AsyncIterator[ExperimentRunner]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `Callable` | (required) | The async experiment function to run. Must be decorated with `@experiment()`. |
| `await_variants` | `bool` | `False` | Whether to wait for variant configurations to complete. |

#### Returns

An async context manager that yields an `ExperimentRunner` instance.

#### Example

```python
@mint.experiment()
async def async_process(input: str, config: dict) -> str:
    await asyncio.sleep(0.1)
    return f"{config['model']}: {input}"

async with Spearmint.arun(async_process) as runner:
    results = await runner("test input")
    print(results.main_result.result)
```

## Module-Level Function

### `experiment()`

Standalone decorator for creating experiments without instantiating Spearmint.

```python
def experiment(
    configs: Sequence[dict[str, Any] | Config | str | Path],
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `configs` | `Sequence` | (required) | List of configurations. |
| `branch_strategy` | `Callable` or `None` | `None` | Strategy for config selection. Reserved for future use. |

#### Example

```python
from spearmint import experiment

@experiment(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"}
])
def generate(prompt: str, config: dict) -> str:
    return f"{config['model']}: {prompt}"

result = generate("Hello")
```

## Usage Patterns

### Pattern 1: Instance-Based (Recommended)

Create a `Spearmint` instance for reusable configuration:

```python
# config.py
from spearmint import Spearmint

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7}
])

# functions.py
from config import mint

@mint.experiment()
def function1(input: str, config: dict) -> str:
    return process1(input, config)

@mint.experiment()
def function2(input: str, config: dict) -> str:
    return process2(input, config)
```

### Pattern 2: Standalone Decorator

For one-off experiments:

```python
from spearmint import experiment

@experiment(configs=[{"param": "value"}])
def standalone_function(input: str, config: dict) -> str:
    return process(input, config)
```

### Pattern 3: Explicit Runners

For fine-grained control:

```python
mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def process(input: str, config: dict) -> str:
    return transform(input, config)

# Synchronous
with Spearmint.run(process) as runner:
    results = runner("input")

# Asynchronous
async with Spearmint.arun(process) as runner:
    results = await runner("input")
```

## Complete Example

```python
from spearmint import Spearmint
from spearmint.configuration import DynamicValue
import asyncio

# Initialize with dynamic configurations
mint = Spearmint(configs=[{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0])
}])
# Creates 6 configurations (2 models × 3 temperatures)

# Sync experiment
@mint.experiment()
def sync_generate(prompt: str, config: dict) -> str:
    return f"{config['model']} (temp={config['temperature']}): {prompt}"

# Async experiment
@mint.experiment()
async def async_generate(prompt: str, config: dict) -> str:
    await asyncio.sleep(0.1)
    return f"{config['model']} (temp={config['temperature']}): {prompt}"

# Use decorator mode
result = sync_generate("Hello world")
print(result)

# Use explicit runner mode
with Spearmint.run(sync_generate) as runner:
    results = runner("Hello world")
    print(f"Main: {results.main_result.result}")
    for variant in results.variant_results:
        print(f"Variant: {variant.result}")

# Use async runner mode
async def main():
    async with Spearmint.arun(async_generate) as runner:
        results = await runner("Hello async")
        print(results.main_result.result)

asyncio.run(main())
```

## See Also

- [Configuration API](configuration.md) - Details on Config and DynamicValue
- [Experiment Function API](experiment-function.md) - Lower-level experiment details
- [Runner API](runner.md) - Execution runtime details
- [Core Concepts](../../getting-started/concepts.md) - High-level overview
