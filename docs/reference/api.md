# API Reference

Complete technical reference for the Spearmint framework API.

## Core Classes

### Spearmint

Main orchestration class for managing experiments and strategies.

``````python
from spearmint import Spearmint
``````

#### Constructor

``````python
Spearmint(
    strategy: type[Strategy] | None = None,
    configs: list[dict | Config | str | Path] | None = None,
    bindings: dict[type[BaseModel], str] | None = None,
    evaluators: Sequence[Callable] | None = None
)
``````

**Parameters:**
- **strategy** (type[Strategy], optional): Strategy class for selecting main config and variants. Defaults to `SingleConfigStrategy`.
- **configs** (list, optional): List of configurations (dicts, YAML files, or Config objects).
- **bindings** (dict, optional): Mapping of Pydantic models to configuration paths (e.g., `{ModelClass: "path.to.config"}`).
- **evaluators** (Sequence[Callable], optional): List of evaluator functions for experiment results.

**Example:**
``````python
from spearmint import Spearmint
from spearmint.strategies import MultiBranchStrategy

mint = Spearmint(
    strategy=MultiBranchStrategy,
    configs=[
        {"model": "gpt-4", "temperature": 0.7},
        {"model": "gpt-3.5-turbo", "temperature": 0.5}
    ]
)
``````

#### Methods

##### `experiment()`

Decorator for wrapping functions with experiment configuration.

``````python
@mint.experiment(
    strategy: type[Strategy] | None = None,
    configs: list | None = None,
    bindings: dict | None = None,
    evaluators: Sequence[Callable] | None = None
)
def your_function(param: str, config: Config) -> ReturnType:
    pass
``````

**Parameters:**
- **strategy** (type[Strategy], optional): Override the instance strategy.
- **configs** (list, optional): Override instance configs.
- **bindings** (dict, optional): Override instance bindings.
- **evaluators** (Sequence[Callable], optional): Set custom evaluators.

**Returns:** Decorated function with experiment capabilities.

**Example:**
``````python
@mint.experiment()
def process_data(input_text: str, config: Config) -> str:
    model = config['model']
    return f"Processed with {model}: {input_text}"
``````

##### `run()` (Static)

Synchronous context manager for executing experiments.

``````python
with Spearmint.run(func, await_variants=False) as runner:
    results = runner(*args, **kwargs)
``````

**Parameters:**
- **func** (Callable): The experiment function to run.
- **await_variants** (bool, optional): Whether to wait for variant results. Defaults to `False`.

**Returns:** `ExperimentRunner` instance.

**Example:**
``````python
@mint.experiment()
def compute(x: int, config: Config) -> int:
    return x * config['multiplier']

with Spearmint.run(compute) as runner:
    result = runner(5)
    print(result.main_result.result)
``````

##### `arun()` (Static)

Asynchronous context manager for executing experiments.

``````python
async with Spearmint.arun(func, await_variants=False) as runner:
    results = await runner(*args, **kwargs)
``````

**Parameters:**
- **func** (Callable): The async experiment function to run.
- **await_variants** (bool, optional): Whether to wait for variant results. Defaults to `False`.

**Returns:** Async `ExperimentRunner` instance.

**Example:**
``````python
@mint.experiment()
async def fetch_data(url: str, config: Config) -> dict:
    # async implementation
    return {"data": "result"}

async def main():
    async with Spearmint.arun(fetch_data) as runner:
        result = await runner("https://api.example.com")
        print(result.main_result.result)
``````

---

## Configuration Classes

### Config

Type-safe configuration model with dictionary-like access.

``````python
from spearmint import Config
``````

**Usage:**
``````python
config = Config({"model": "gpt-4", "temperature": 0.7})

# Dictionary-like access
model = config['model']
temp = config['temperature']

# Nested access
config = Config({"llm": {"model": "gpt-4"}})
model = config['llm']['model']
``````

**Note:** Config is a Pydantic `RootModel` that provides type safety while maintaining dict-like interface.

---

### DynamicValue[T]

Generic wrapper for iterables that enables configuration sweeping.

``````python
from spearmint.config import DynamicValue
``````

**Constructor:**
``````python
DynamicValue(iterable: Iterable[T])
``````

**Parameters:**
- **iterable** (Iterable[T]): Any iterable (list, range, generator) of configuration values.

**Example:**
``````python
from spearmint.config import DynamicValue

# Expands to multiple configs via cartesian product
configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0])
}]
# Creates 6 configurations (2 models × 3 temperatures)

mint = Spearmint(configs=configs)
``````

**With generators:**
``````python
def temp_range():
    for temp in range(0, 101, 25):
        yield temp / 100.0

configs = [{"temperature": DynamicValue(temp_range())}]
# Creates 5 configurations: 0.0, 0.25, 0.5, 0.75, 1.0
``````

---

## Configuration Binding

### Bind

Decorator for binding configuration paths to typed Pydantic models.

``````python
from spearmint.config import Bind
from typing import Annotated
``````

**Usage:**
``````python
from pydantic import BaseModel
from typing import Annotated
from spearmint import Spearmint
from spearmint.config import Bind

class LLMConfig(BaseModel):
    model: str
    temperature: float

mint = Spearmint(configs=[{
    "llm": {"model": "gpt-4", "temperature": 0.7}
}])

@mint.experiment()
def generate(
    prompt: str,
    config: Annotated[LLMConfig, Bind("llm")]
) -> str:
    # config is typed as LLMConfig with IDE support
    return f"{config.model}: {prompt}"
``````

**Path notation:**
- Use dot notation for nested paths: `"path.to.nested.config"`
- Use empty string `""` for root-level binding

---

## Execution & Context

### ExperimentRunner

Manages execution of experiments with main and variant configurations.

**Attributes:**
- **main_result**: Result from the primary configuration
- **variant_results**: List of results from variant configurations (if `await_variants=True`)

**Methods:**
- **`__call__(*args, **kwargs)`**: Execute the experiment with given arguments

**Example:**
``````python
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner("input")
    
    print(f"Main: {results.main_result.result}")
    for variant in results.variant_results:
        print(f"Variant: {variant.result}")
``````

---

### ExperimentCase

Holds configuration mapping for a specific experiment execution path.

**Attributes:**
- **config** (dict): The configuration dictionary
- **config_id** (str): Unique identifier for the configuration (SHA256 hash)

---

### RuntimeContext

Context manager for runtime variables during execution. Uses Python `contextvars` for async-safe state management.

**Usage (Internal):**
``````python
from spearmint.context import RuntimeContext

with RuntimeContext(experiment_case):
    # Experiment code executes here
    pass
``````

---

## Configuration Utilities

### parse_configs()

Parses multiple configuration sources into standardized format.

``````python
from spearmint.configuration import parse_configs

configs = parse_configs(
    configs: list[dict | str | Path | Config],
    config_handler: Callable[[Path], list[dict]] = yaml_handler
) -> list[dict]
``````

**Parameters:**
- **configs** (list): List of config sources (dicts, file paths, Config objects)
- **config_handler** (Callable, optional): Function to load files. Defaults to `yaml_handler`.

**Returns:** List of configuration dictionaries.

**Supports:**
- Python dictionaries
- YAML files (`.yaml`, `.yml`)
- JSONL files (`.jsonl`)
- Directories (loads all YAML files recursively)
- Config objects

**Example:**
``````python
configs = parse_configs([
    {"model": "gpt-4"},           # Dict
    "config.yaml",                 # Single file
    "configs/",                    # Directory
])
``````

---

### generate_configurations()

Expands `DynamicValue` fields into cartesian product of configurations.

``````python
from spearmint.configuration import generate_configurations

expanded = generate_configurations(config: dict) -> list[dict]
``````

**Parameters:**
- **config** (dict): Configuration with potential `DynamicValue` fields

**Returns:** List of all possible configuration combinations.

**Example:**
``````python
from spearmint.config import DynamicValue

config = {
    "model": DynamicValue(["gpt-4", "gpt-3.5"]),
    "temperature": DynamicValue([0.0, 0.5])
}

configs = generate_configurations(config)
# Returns:
# [
#   {"model": "gpt-4", "temperature": 0.0},
#   {"model": "gpt-4", "temperature": 0.5},
#   {"model": "gpt-3.5", "temperature": 0.0},
#   {"model": "gpt-3.5", "temperature": 0.5}
# ]
``````

---

## File Handlers

### yaml_handler()

Loads YAML files or directories into configuration dictionaries.

``````python
from spearmint.utils.handlers import yaml_handler

configs = yaml_handler(file_path: Path) -> list[dict]
``````

**Parameters:**
- **file_path** (Path): Path to YAML file or directory

**Returns:** List of configuration dictionaries.

**Behavior:**
- Single file: Returns list with one config
- Directory: Recursively loads all `.yaml` and `.yml` files

---

### jsonl_handler()

Loads JSONL (JSON Lines) files into configuration dictionaries.

``````python
from spearmint.utils.handlers import jsonl_handler

configs = jsonl_handler(file_path: Path) -> list[dict]
``````

**Parameters:**
- **file_path** (Path): Path to JSONL file

**Returns:** List of configuration dictionaries (one per line).

---

## Registry

### ExperimentFunctionRegistry

Global registry tracking all decorated experiment functions.

**Methods:**
- **`register(func, experiment_func)`**: Register a function
- **`get(func)`**: Retrieve experiment function details
- **`contains(func)`**: Check if function is registered

**Usage (Internal):**
``````python
from spearmint.registry import ExperimentFunctionRegistry

registry = ExperimentFunctionRegistry()
``````

**Note:** Registry is primarily for internal use. The `@experiment` decorator automatically registers functions.

---

## Type Hints

Common type annotations used throughout the framework:

``````python
from typing import Any, Callable, Sequence
from pathlib import Path
from pydantic import BaseModel

# Config types
ConfigSource = dict | Config | str | Path
ConfigList = list[ConfigSource]

# Strategy function signature
Strategy = Callable[[list[dict]], tuple[dict, list[dict]]]

# Evaluator function signature
Evaluator = Callable[[Any, dict], float]
``````

---

## See Also

- [Configuration System](configuration.md) - Deep dive into config management
- [Strategies](strategies.md) - Available execution strategies
- [Runners](runners.md) - Execution context managers
