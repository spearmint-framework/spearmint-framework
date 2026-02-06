# Runners & Context Managers

Execution context managers for Spearmint experiments.

## Overview

Runners provide structured execution of experiments with access to detailed results.

## Synchronous Runner

### Basic Usage

``````python
with Spearmint.run(my_function) as runner:
    result = runner(*args, **kwargs)
    print(result.main_result.result)
``````

### Await Variants

``````python
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner(*args)
    
    # Access main result
    print(results.main_result.result)
    
    # Access variant results
    for variant in results.variant_results:
        print(variant.result)
``````

## Asynchronous Runner

### Basic Usage

``````python
async with Spearmint.arun(my_async_function) as runner:
    result = await runner(*args, **kwargs)
    print(result.main_result.result)
``````

## Result Objects

### ExperimentResult

Returned from runner execution:

- **main_result**: Result from primary config
- **variant_results**: List of variant results
- **duration**: Total execution time
- **status**: Success/failure status

### Branch Result

Individual config result:

- **result**: Function return value
- **config**: Configuration used
- **config_id**: Config identifier
- **duration**: Execution time
- **exception_info**: Error details if failed

## See Also

- [API Reference](api.md)
- [Strategies](strategies.md)
