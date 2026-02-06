# Runner APIs

The Runner APIs provide direct control over experiment execution, allowing access to both primary and variant results.

## Overview

There are two runner APIs:
- **`Spearmint.run()`** - Synchronous experiment execution
- **`Spearmint.arun()`** - Asynchronous experiment execution

Both return context managers that yield a runner function you can call multiple times within the context.

## Spearmint.run

Execute synchronous experiments with full control over variant execution.

### Signature

``````python
@staticmethod
@contextmanager
def run(
    func: Callable[..., Any],
    await_variants: bool = False
) -> Iterator[Callable[..., ExperimentCaseResults]]
``````

### Parameters

#### `func`
**Type:** `Callable[..., Any]`  
**Required:** Yes

The experiment function to run. Must be decorated with `@mint.experiment()` or `@experiment()`.

#### `await_variants`
**Type:** `bool`  
**Default:** `False`

Controls variant execution behavior:
- **`False`**: Variants run in background daemon threads (fire-and-forget)
- **`True`**: Waits for all variants to complete before returning

### Returns

**Type:** `Iterator[Callable[..., ExperimentCaseResults]]`

Yields a runner function that accepts the same arguments as the original function and returns an `ExperimentCaseResults` object.

### Example: Basic Usage

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def generate_text(prompt: str, config: Config) -> str:
    return f"Generated with {config['model']}: {prompt}"

# Execute and access results
with Spearmint.run(generate_text) as runner:
    results = runner("Hello world")
    print(results.main_result.result)
``````

### Example: Awaiting Variants

``````python
mint = Spearmint(configs=[
    {"model": "gpt-4o"},
    {"model": "gpt-4o-mini"},
    {"model": "gpt-3.5-turbo"}
])

@mint.experiment()
def compare_models(prompt: str, config: Config) -> str:
    return f"{config['model']}: {prompt}"

# Wait for all variants
with Spearmint.run(compare_models, await_variants=True) as runner:
    results = runner("Compare these models")
    
    # Access primary result
    print("Primary:", results.main_result.result)
    
    # Access all variant results
    for variant in results.variant_results:
        print("Variant:", variant.result)
``````

### Example: Multiple Calls

You can call the runner multiple times within the same context:

``````python
with Spearmint.run(generate_text) as runner:
    result1 = runner("First prompt")
    result2 = runner("Second prompt")
    result3 = runner("Third prompt")
    
    print(result1.main_result.result)
    print(result2.main_result.result)
    print(result3.main_result.result)
``````

## Spearmint.arun

Execute asynchronous experiments with full control over variant execution.

### Signature

``````python
@staticmethod
@asynccontextmanager
async def arun(
    func: Callable[..., Any],
    await_variants: bool = False
) -> AsyncIterator[Callable[..., Awaitable[ExperimentCaseResults]]]
``````

### Parameters

#### `func`
**Type:** `Callable[..., Any]`  
**Required:** Yes

The async experiment function to run. Must be decorated with `@mint.experiment()` and defined with `async def`.

#### `await_variants`
**Type:** `bool`  
**Default:** `False`

Controls variant execution behavior:
- **`False`**: Variants run as background asyncio tasks
- **`True`**: Waits for all variant tasks to complete

### Returns

**Type:** `AsyncIterator[Callable[..., Awaitable[ExperimentCaseResults]]]`

Yields an async runner function that must be awaited.

### Example: Basic Async Usage

``````python
import asyncio
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
async def async_generate(prompt: str, config: Config) -> str:
    await asyncio.sleep(0.1)  # Simulate async work
    return f"Generated: {prompt}"

async def main():
    async with Spearmint.arun(async_generate) as runner:
        results = await runner("Hello async")
        print(results.main_result.result)

asyncio.run(main())
``````

### Example: Async with Variants

``````python
mint = Spearmint(configs=[
    {"model": "gpt-4o", "delay": 0.1},
    {"model": "gpt-4o-mini", "delay": 0.05}
])

@mint.experiment()
async def async_compare(prompt: str, config: Config) -> str:
    await asyncio.sleep(config['delay'])
    return f"{config['model']}: {prompt}"

async def main():
    async with Spearmint.arun(async_compare, await_variants=True) as runner:
        results = await runner("Compare")
        
        print("Primary:", results.main_result.result)
        for variant in results.variant_results:
            print("Variant:", variant.result)

asyncio.run(main())
``````

## ExperimentCaseResults

The result object returned by both runner APIs.

### Structure

``````python
@dataclass
class ExperimentCaseResults:
    main_result: FunctionResult
    variant_results: list[FunctionResult]
``````

### Attributes

#### `main_result`
**Type:** `FunctionResult`

The result from the primary configuration.

#### `variant_results`
**Type:** `list[FunctionResult]`

Results from variant configurations. Empty list if no variants or `await_variants=False`.

## FunctionResult

Individual result from a configuration.

### Structure

``````python
@dataclass
class FunctionResult:
    result: Any
    experiment_case: ExperimentCase
``````

### Attributes

#### `result`
**Type:** `Any`

The return value from the function execution.

#### `experiment_case`
**Type:** `ExperimentCase`

The experiment case containing configuration information.

### Example: Accessing Configuration

``````python
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner("test")
    
    # Get config ID from result
    config_id = results.main_result.experiment_case.get_config_id(my_function.__qualname__)
    print(f"Primary used config: {config_id}")
``````

## Comparison: Direct Call vs Runner

### Direct Call

``````python
@mint.experiment()
def my_function(config: Config) -> str:
    return config['model']

# Returns only primary result
result = my_function()  # str
``````

### Using Runner

``````python
@mint.experiment()
def my_function(config: Config) -> str:
    return config['model']

# Returns ExperimentCaseResults with all results
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner()  # ExperimentCaseResults
    primary = results.main_result.result  # str
    variants = [v.result for v in results.variant_results]  # list[str]
``````

## Use Cases

### When to Use Direct Calls

- Production code where you only need the primary result
- Simple experiments without variant analysis
- When variants are fire-and-forget background tracking

``````python
@mint.experiment()
def production_endpoint(request: str, config: Config) -> Response:
    return process(request, config)

# Direct call in API handler
response = production_endpoint(user_request)
``````

### When to Use Runners

- Offline evaluation and comparison
- When you need to analyze all variant results
- Batch processing with detailed logging
- Testing and validation

``````python
@mint.experiment()
def evaluation_function(data: dict, config: Config) -> dict:
    return evaluate(data, config)

# Compare all configurations
with Spearmint.run(evaluation_function, await_variants=True) as runner:
    results = runner(test_data)
    
    # Analyze all results
    for variant in results.variant_results:
        log_metrics(variant.result)
``````

## Thread Safety and Context Propagation

Both runners properly handle:
- Context variable propagation to threads/tasks
- Experiment case isolation
- Configuration injection

``````python
# Context is properly isolated per call
with Spearmint.run(my_function) as runner:
    result1 = runner("call 1")  # Gets its own context
    result2 = runner("call 2")  # Gets its own context
``````

## See Also

- [Experiment Decorator](experiment.md) - Function decoration
- [Results](results.md) - Detailed result structure
- [ExperimentCase](experiment-case.md) - Configuration case details
- [FunctionResult](function-result.md) - Individual result details
