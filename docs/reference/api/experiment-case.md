# ExperimentCase

Container for configuration mappings and metadata for an experiment execution.

## Overview

`ExperimentCase` tracks which configurations are used for which functions in an experiment, especially important for nested experiments.

## Structure

``````python
class ExperimentCase:
    """Tracks configuration assignments for experiment functions."""
    
    def __init__(self, func_name: str, config: Config) -> None:
        """Initialize with a function name and its config."""
        self.config_map: dict[str, str]
        self._configs: dict[str, Config]
    
    def add(self, func_name: str, config: Config) -> None:
        """Add a function-config mapping."""
        ...
    
    def get_config_id(self, func_name: str) -> str:
        """Get the config ID for a function."""
        ...
``````

## Attributes

### `config_map`
**Type:** `dict[str, str]`

Maps function qualified names to config IDs:

``````python
{
    "module.ClassName.method_name": "abc123def456",
    "module.other_function": "def789ghi012"
}
``````

### `_configs`
**Type:** `dict[str, Config]`

Internal storage of Config objects by their config_id.

## Methods

### `get_config_id`

Get the configuration ID used for a specific function.

#### Signature

``````python
def get_config_id(self, func_name: str) -> str
``````

#### Parameters

- **`func_name`** (`str`): Qualified name of the function

#### Returns

`str`: The config ID for that function

#### Raises

`ValueError`: If no config found for the function

#### Example

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def my_function(config: Config) -> str:
    return config['model']

with Spearmint.run(my_function) as runner:
    results = runner()
    
    # Get config ID from experiment case
    func_qualname = my_function.__qualname__
    config_id = results.main_result.experiment_case.get_config_id(func_qualname)
    print(f"Used config: {config_id}")
``````

### `add`

Add a function-config mapping to the experiment case.

#### Signature

``````python
def add(self, func_name: str, config: Config) -> None
``````

#### Parameters

- **`func_name`** (`str`): Qualified name of the function
- **`config`** (`Config`): Configuration to associate with the function

#### Example

Used internally by Spearmint when setting up nested experiments.

## Use Cases

### Simple Experiment

For a single-function experiment:

``````python
mint = Spearmint(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"}
])

@mint.experiment()
def single_function(config: Config) -> str:
    return config['model']

with Spearmint.run(single_function, await_variants=True) as runner:
    results = runner()
    
    # Main result's experiment case
    main_case = results.main_result.experiment_case
    main_config_id = main_case.get_config_id(single_function.__qualname__)
    
    # Each variant has its own case
    for variant in results.variant_results:
        variant_case = variant.experiment_case
        variant_config_id = variant_case.get_config_id(single_function.__qualname__)
        print(f"Variant used: {variant_config_id}")
``````

### Nested Experiments

For nested experiments, the case tracks configs for all involved functions:

``````python
mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def inner_function(text: str, config: Config) -> str:
    return f"Inner: {config['model']}"

@mint.experiment()
def outer_function(text: str, config: Config) -> str:
    inner_result = inner_function(text)
    return f"Outer: {config['model']}, {inner_result}"

with Spearmint.run(outer_function) as runner:
    results = runner("test")
    
    case = results.main_result.experiment_case
    
    # Get configs for both functions
    outer_config_id = case.get_config_id(outer_function.__qualname__)
    inner_config_id = case.get_config_id(inner_function.__qualname__)
    
    print(f"Outer config: {outer_config_id}")
    print(f"Inner config: {inner_config_id}")
``````

## Function Qualified Names

Use `__qualname__` to get the correct function identifier:

``````python
# Module-level function
def module_function(config: Config) -> str:
    return "result"

# Class method
class MyClass:
    @mint.experiment()
    def method(self, config: Config) -> str:
        return "result"

# Qualified names
print(module_function.__qualname__)  # "module_function"
print(MyClass.method.__qualname__)   # "MyClass.method"

# Use with experiment case
case.get_config_id(module_function.__qualname__)
case.get_config_id(MyClass.method.__qualname__)
``````

## Error Handling

### Function Not Found

``````python
mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def my_function(config: Config) -> str:
    return "result"

with Spearmint.run(my_function) as runner:
    results = runner()
    
    try:
        # Wrong function name
        config_id = results.main_result.experiment_case.get_config_id("wrong_name")
    except ValueError as e:
        print(f"Error: {e}")  # "No config found for function 'wrong_name'"
``````

## Internal Usage

`ExperimentCase` is primarily used internally by Spearmint to:
1. Track configuration assignments during experiment execution
2. Support nested experiments with multiple configurations
3. Provide configuration context in results

Most users interact with it only through `FunctionResult.experiment_case`.

## Complete Example

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[
    {"id": 1, "model": "gpt-4"},
    {"id": 2, "model": "gpt-3.5-turbo"},
    {"id": 3, "model": "gpt-4o-mini"}
])

@mint.experiment()
def evaluate(text: str, config: Config) -> dict:
    return {
        "config_id": config['id'],
        "model": config['model'],
        "result": f"Evaluated by {config['model']}"
    }

with Spearmint.run(evaluate, await_variants=True) as runner:
    results = runner("test text")
    
    # Process all results with config tracking
    all_results = [results.main_result] + results.variant_results
    
    for func_result in all_results:
        # Get config ID from experiment case
        case = func_result.experiment_case
        config_id = case.get_config_id(evaluate.__qualname__)
        
        # Get actual result
        result = func_result.result
        
        print(f"Config {config_id}: {result['model']}")
        print(f"  Result: {result['result']}")
``````

## See Also

- [FunctionResult](function-result.md) - Result wrapper containing ExperimentCase
- [Results](results.md) - Overall result structure
- [Nested Experiments](../../how-to/nested-experiments.md) - Using nested experiments
- [Config Object](config.md) - Configuration structure
