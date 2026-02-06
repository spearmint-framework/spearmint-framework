# FunctionResult

Detailed structure of individual experiment results.

## Overview

`FunctionResult` wraps the return value from a single configuration execution along with its experiment context.

## Structure

``````python
from dataclasses import dataclass
from typing import Any

@dataclass
class FunctionResult:
    """Result from executing an experiment with a specific configuration."""
    result: Any
    experiment_case: ExperimentCase
``````

## Attributes

### `result`
**Type:** `Any`

The actual return value from the experiment function when executed with this configuration.

**Example:**
``````python
@mint.experiment()
def my_function(config: Config) -> str:
    return f"Output: {config['model']}"

with Spearmint.run(my_function) as runner:
    results = runner()
    
    # result contains the string returned by my_function
    print(results.main_result.result)  # "Output: gpt-4"
``````

### `experiment_case`
**Type:** `ExperimentCase`

The experiment case that was used for this execution. Contains:
- Configuration ID mapping
- Configuration objects
- Function name associations

**Example:**
``````python
with Spearmint.run(my_function) as runner:
    results = runner()
    
    # Access experiment case
    case = results.main_result.experiment_case
    config_id = case.get_config_id(my_function.__qualname__)
    print(f"Used config: {config_id}")
``````

## Usage Patterns

### Extracting Results

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"}
])

@mint.experiment()
def process(text: str, config: Config) -> dict:
    return {
        "model": config['model'],
        "processed": f"Processed by {config['model']}"
    }

with Spearmint.run(process, await_variants=True) as runner:
    results = runner("test text")
    
    # Extract all results
    all_outputs = [results.main_result.result]
    all_outputs.extend(v.result for v in results.variant_results)
    
    for output in all_outputs:
        print(f"{output['model']}: {output['processed']}")
``````

### Comparing Results

``````python
@mint.experiment()
def evaluate(data: dict, config: Config) -> float:
    # Return a score
    return calculate_score(data, config)

with Spearmint.run(evaluate, await_variants=True) as runner:
    results = runner(test_data)
    
    # Compare scores
    main_score = results.main_result.result
    variant_scores = [v.result for v in results.variant_results]
    
    best_score = max([main_score] + variant_scores)
    print(f"Best score: {best_score}")
``````

### Logging Results with Config Info

``````python
import logging

logger = logging.getLogger(__name__)

@mint.experiment()
def logged_function(input: str, config: Config) -> str:
    return process(input, config)

with Spearmint.run(logged_function, await_variants=True) as runner:
    results = runner("test input")
    
    # Log with config information
    for func_result in [results.main_result] + results.variant_results:
        config_id = func_result.experiment_case.get_config_id(
            logged_function.__qualname__
        )
        logger.info(
            f"Config {config_id}: {func_result.result}"
        )
``````

## Type Annotations

For better type safety, use type variables:

``````python
from typing import TypeVar
from spearmint import Spearmint, Config

T = TypeVar('T')

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def typed_function(config: Config) -> str:
    return f"Result: {config['model']}"

with Spearmint.run(typed_function) as runner:
    results = runner()
    
    # Type hint the result
    main_result: FunctionResult = results.main_result
    return_value: str = main_result.result
``````

## Handling Different Return Types

### Simple Values

``````python
@mint.experiment()
def returns_string(config: Config) -> str:
    return "simple string"

with Spearmint.run(returns_string) as runner:
    results = runner()
    value: str = results.main_result.result
``````

### Complex Objects

``````python
from dataclasses import dataclass

@dataclass
class Response:
    text: str
    tokens: int
    model: str

@mint.experiment()
def returns_object(config: Config) -> Response:
    return Response(
        text="Generated text",
        tokens=42,
        model=config['model']
    )

with Spearmint.run(returns_object) as runner:
    results = runner()
    response: Response = results.main_result.result
    print(f"Model: {response.model}, Tokens: {response.tokens}")
``````

### Lists and Collections

``````python
@mint.experiment()
def returns_list(config: Config) -> list[str]:
    return ["item1", "item2", "item3"]

with Spearmint.run(returns_list) as runner:
    results = runner()
    items: list[str] = results.main_result.result
    print(f"Got {len(items)} items")
``````

## Error Scenarios

### Function Raised Exception

When the function raises an exception:

``````python
@mint.experiment()
def may_fail(config: Config) -> str:
    if config.get('fail'):
        raise ValueError("Intentional failure")
    return "Success"

# Primary fails
mint = Spearmint(configs=[{"fail": True}])
try:
    with Spearmint.run(may_fail) as runner:
        results = runner()  # Raises ValueError
except ValueError as e:
    print(f"Primary failed: {e}")
``````

### Variant Exception

``````python
mint = Spearmint(configs=[
    {"fail": False},  # Primary
    {"fail": True}    # Variant
])

@mint.experiment()
def may_fail(config: Config) -> str:
    if config.get('fail'):
        raise ValueError("Variant failure")
    return "Success"

# Primary succeeds, variant failure logged
with Spearmint.run(may_fail) as runner:
    results = runner()
    print(results.main_result.result)  # "Success"
    # Variant exception is logged, not in variant_results
``````

## Relationship to ExperimentCase

Each `FunctionResult` includes an `ExperimentCase` that provides configuration context:

``````python
@mint.experiment()
def my_function(config: Config) -> str:
    return config['model']

with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner()
    
    # Each result has its own experiment case
    main_case = results.main_result.experiment_case
    main_config_id = main_case.get_config_id(my_function.__qualname__)
    
    for variant in results.variant_results:
        variant_case = variant.experiment_case
        variant_config_id = variant_case.get_config_id(my_function.__qualname__)
        print(f"Variant config: {variant_config_id}")
``````

## See Also

- [Results](results.md) - Overall result structure
- [ExperimentCase](experiment-case.md) - Configuration case details
- [Runner APIs](runner.md) - Executing experiments
- [Experiment Decorator](experiment.md) - Function decoration
