# Results

Result structures returned by experiment execution.

## Overview

Spearmint returns different result types depending on how you execute experiments:

- **Direct call**: Returns only the primary result value
- **With runner**: Returns `ExperimentCaseResults` with all results

## ExperimentCaseResults

Complete results from an experiment execution including primary and variant results.

### Structure

``````python
from dataclasses import dataclass

@dataclass
class ExperimentCaseResults:
    """Results from running an experiment."""
    main_result: FunctionResult
    variant_results: list[FunctionResult]
``````

### Attributes

#### `main_result`
**Type:** `FunctionResult`

The result from the primary configuration (first config or as determined by branch strategy).

#### `variant_results`
**Type:** `list[FunctionResult]`

Results from variant configurations. Populated only when using runners with `await_variants=True`.

### Example

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"}
])

@mint.experiment()
def my_function(config: Config) -> str:
    return f"Result from {config['model']}"

# Get full results
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner()  # ExperimentCaseResults
    
    print(results.main_result.result)  # "Result from gpt-4"
    print(results.variant_results[0].result)  # "Result from gpt-3.5-turbo"
``````

## FunctionResult

Individual result from a single configuration execution.

### Structure

``````python
from dataclasses import dataclass

@dataclass
class FunctionResult:
    """Result from a single configuration execution."""
    result: Any
    experiment_case: ExperimentCase
``````

### Attributes

#### `result`
**Type:** `Any`

The actual return value from the experiment function for this configuration.

#### `experiment_case`
**Type:** `ExperimentCase`

The experiment case containing configuration IDs and mapping information.

### Example

``````python
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner("test input")
    
    # Access main result
    main = results.main_result
    print(f"Result: {main.result}")
    print(f"Config ID: {main.experiment_case.get_config_id(my_function.__qualname__)}")
    
    # Access variant results
    for variant in results.variant_results:
        print(f"Variant result: {variant.result}")
``````

## Direct Call Returns

When calling an experiment function directly (not through a runner), only the primary result value is returned:

``````python
mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def my_function(config: Config) -> str:
    return f"Result from {config['model']}"

# Direct call
result = my_function()  # str: "Result from gpt-4"
# NOT ExperimentCaseResults - just the return value
``````

## Runner Returns

Using runners gives access to full result structure:

### Synchronous

``````python
with Spearmint.run(my_function) as runner:
    results = runner()  # ExperimentCaseResults
    value = results.main_result.result  # Actual return value
``````

### Asynchronous

``````python
async with Spearmint.arun(my_function) as runner:
    results = await runner()  # ExperimentCaseResults
    value = results.main_result.result  # Actual return value
``````

## Accessing Configuration Information

Each `FunctionResult` includes the `ExperimentCase` which contains configuration details:

``````python
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner()
    
    # Get config ID for main result
    func_qualname = my_function.__qualname__
    main_config_id = results.main_result.experiment_case.get_config_id(func_qualname)
    print(f"Main config ID: {main_config_id}")
    
    # Get config IDs for variants
    for variant in results.variant_results:
        variant_config_id = variant.experiment_case.get_config_id(func_qualname)
        print(f"Variant config ID: {variant_config_id}")
``````

## Empty Variant Results

When `await_variants=False` (default), variants run in background and `variant_results` is empty:

``````python
mint = Spearmint(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"},
    {"model": "gpt-4o-mini"}
])

@mint.experiment()
def my_function(config: Config) -> str:
    return config['model']

# Default: variants run in background
with Spearmint.run(my_function) as runner:
    results = runner()
    
    print(results.main_result.result)  # "gpt-4"
    print(len(results.variant_results))  # 0 (running in background)
``````

## Complete Example

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7},
    {"model": "gpt-3.5-turbo", "temperature": 0.5},
    {"model": "gpt-4o-mini", "temperature": 0.9}
])

@mint.experiment()
def generate_summary(text: str, config: Config) -> dict:
    return {
        "model": config['model'],
        "temperature": config['temperature'],
        "summary": f"Summary by {config['model']}"
    }

# Execute and collect all results
with Spearmint.run(generate_summary, await_variants=True) as runner:
    results = runner("Long article text...")
    
    # Process main result
    main = results.main_result.result
    print(f"Primary: {main['model']} - {main['summary']}")
    
    # Process all variants
    all_results = [main] + [v.result for v in results.variant_results]
    
    for result in all_results:
        print(f"{result['model']} (temp={result['temperature']}): {result['summary']}")
    
    # Compare results
    best_model = max(all_results, key=lambda r: len(r['summary']))
    print(f"Most verbose: {best_model['model']}")
``````

## Error Handling

### Primary Result Exceptions

Exceptions in the primary function propagate to caller:

``````python
@mint.experiment()
def failing_function(config: Config) -> str:
    raise ValueError("Error occurred")

try:
    with Spearmint.run(failing_function) as runner:
        results = runner()
except ValueError as e:
    print(f"Primary failed: {e}")
``````

### Variant Result Exceptions

Variant exceptions are logged but don't raise (unless using `await_variants=True`):

``````python
mint = Spearmint(configs=[
    {"model": "working"},
    {"model": "broken"}
])

@mint.experiment()
def sometimes_fails(config: Config) -> str:
    if config['model'] == "broken":
        raise ValueError("This variant fails")
    return f"Success: {config['model']}"

# With await_variants=False (default)
with Spearmint.run(sometimes_fails) as runner:
    results = runner()  # Primary succeeds, variant logged as failed
    print(results.main_result.result)  # "Success: working"

# With await_variants=True
try:
    with Spearmint.run(sometimes_fails, await_variants=True) as runner:
        results = runner()  # May raise if variant fails
except ValueError as e:
    print(f"A variant failed: {e}")
``````

## Type Hints

For type safety, annotate runner returns:

``````python
from spearmint import Spearmint, Config

@mint.experiment()
def typed_function(config: Config) -> str:
    return f"Result: {config['model']}"

# With type hints
with Spearmint.run(typed_function) as runner:
    results: ExperimentCaseResults = runner()
    main_value: str = results.main_result.result
    
    for variant in results.variant_results:
        variant_value: str = variant.result
``````

## See Also

- [FunctionResult](function-result.md) - Detailed FunctionResult structure
- [ExperimentCase](experiment-case.md) - Configuration case details
- [Runner APIs](runner.md) - Experiment execution
- [Experiment Decorator](experiment.md) - Function decoration
