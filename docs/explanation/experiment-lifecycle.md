# Experiment Lifecycle

Understanding what happens when you call an experiment function.

## Overview

When you decorate a function with `@experiment` and call it, Spearmint executes a multi-stage lifecycle involving configuration selection, context setup, execution, and result collection. This document explains each stage in detail.

## Lifecycle Stages

### 1. Decoration Phase (Setup)

Happens once when the module is imported.

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()  # <-- Decoration happens here
def generate(prompt: str, config: Config) -> str:
    return f"{config['model']}: {prompt}"
``````

**What happens:**
1. **Configuration parsing:** `configs` are parsed into `Config` objects
   - YAML files are loaded
   - Dictionaries are wrapped in `Config` objects
   - Config IDs are generated (e.g., `"gpt-4-0.7"`)

2. **ExperimentFunction creation:** Original function is wrapped in `ExperimentFunction`
   - Function signature is inspected
   - Config parameter is identified
   - Async vs sync is detected

3. **Registry registration:** Function is registered in `experiment_fn_registry`
   - Global tracking for nested experiments
   - Discovery of inner function calls via AST

4. **Wrapper creation:** A new function is returned
   - Sync functions get `swrapper`
   - Async functions get `awrapper`
   - Original function's `__name__` and `__doc__` are preserved

### 2. Call Phase (Invocation)

Happens every time you call the decorated function.

``````python
result = generate("Hello")  # <-- Call happens here
``````

**What happens:**

#### 2a. Runner Context Setup

``````python
with run_experiment(func) as runner:
    # Runner setup happens here
    pass
``````

1. **Retrieve ExperimentFunction:** Look up in registry by function qualname
2. **Create ExperimentCases:** Map each config to an `ExperimentCase`
3. **Branch strategy execution:** Determine primary vs variant configs
   ``````python
   primary_config, variant_configs = branch_strategy(*args, **kwargs)
   ``````
4. **Context variable setup:** Initialize `experiment_runner` context var

#### 2b. Primary Execution

``````python
results = runner(*args, **kwargs)  # <-- Actual execution
``````

**Steps:**
1. **Identify primary case:** First config (by default) becomes primary
2. **Set context:** `current_experiment_case` context var is set
3. **Config injection:** Prepare `config` parameter for function
4. **Execute function:** Call original function with injected config
   ``````python
   result = original_func(prompt, config=primary_config)
   ``````
5. **Capture result:** Store return value in `FunctionResult`
6. **Exception handling:** Catch and store any exceptions

#### 2c. Variant Execution (Parallel)

If multiple configs exist, variants run concurrently.

**For sync functions:**
``````python
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(run_variant, case) for case in variant_cases]
``````

**For async functions:**
``````python
tasks = [asyncio.create_task(run_variant(case)) for case in variant_cases]
``````

**Each variant:**
1. Gets its own context (`current_experiment_case`)
2. Executes independently
3. Captures results or exceptions
4. Runs in background (doesn't block primary)

#### 2d. Result Collection

``````python
return ExperimentCaseResults(
    main_result=primary_result,
    variant_results=variant_results
)
``````

**Result structure:**
``````python
results.main_result.result              # Actual return value
results.main_result.experiment_case     # Config used
results.variant_results                 # List of variant results
``````

### 3. Cleanup Phase

Happens when execution completes.

``````python
# Context manager exit
``````

**What happens:**
1. **Context variables reset:** `current_experiment_case` and `experiment_runner` cleared
2. **Resource cleanup:** Thread pool or async tasks are shut down
3. **Return final results:** Primary result is returned to caller

## Detailed Example

``````python
from spearmint import Spearmint, Config
import time

mint = Spearmint(configs=[
    {"model": "gpt-4", "temp": 0.7},
    {"model": "gpt-3.5-turbo", "temp": 0.5}
])

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    print(f"[{config['model']}] Processing: {prompt}")
    time.sleep(0.1)  # Simulate API call
    return f"Result from {config['model']}"

# Call the function
result = generate("Hello world")
print(f"Got: {result}")
``````

**Timeline:**

``````
T+0ms:  Decorator executes
        - Parse 2 configs
        - Create ExperimentFunction
        - Register in global registry
        - Return wrapped function

T+100ms: User calls generate("Hello world")
         - Enter runner context
         - Identify primary: {"model": "gpt-4", "temp": 0.7}
         - Identify variant: {"model": "gpt-3.5-turbo", "temp": 0.5}

T+101ms: Execute primary
         - Set context: current_experiment_case = case[0]
         - Inject config[0]
         - Call generate("Hello world", config=config[0])
         - Print: [gpt-4] Processing: Hello world
         
T+102ms: Start variant (in thread)
         - Set context: current_experiment_case = case[1]
         - Inject config[1]
         - Call generate("Hello world", config=config[1])
         - Print: [gpt-3.5-turbo] Processing: Hello world

T+201ms: Primary completes
         - Return "Result from gpt-4"
         - Store in FunctionResult
         
T+202ms: Variant completes (in background)
         - Return "Result from gpt-3.5-turbo"
         - Store in variant results

T+203ms: Exit runner context
         - Collect all results
         - Return ExperimentCaseResults
         - Primary result returned to caller

T+204ms: User receives result
         - result == "Result from gpt-4"
``````

## Context Isolation

Each execution gets isolated context:

``````python
from spearmint import Spearmint, Config
from spearmint.context import current_experiment_case

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def inner(config: Config) -> str:
    # This sees the correct config even if called from another experiment
    case = current_experiment_case.get()
    return f"Inner: {case.config.id}"

@mint.experiment()
def outer(config: Config) -> str:
    result = inner()  # Nested call
    return f"Outer: {config.id}, {result}"
``````

**How it works:**
- `contextvars` provide thread-local and task-local storage
- Each `ExperimentCase` gets its own context
- Nested calls see their own config, not the parent's

## Async Lifecycle

Async functions follow the same lifecycle with async-specific handling:

``````python
import asyncio
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
async def async_generate(prompt: str, config: Config) -> str:
    await asyncio.sleep(0.1)
    return f"Async result: {prompt}"

# Lifecycle
async def main():
    result = await async_generate("Hello")  # Async wrapper
    print(result)
    
asyncio.run(main())
``````

**Differences:**
1. **Wrapper type:** Uses `awrapper` instead of `swrapper`
2. **Runner type:** Uses `run_experiment_async` context manager
3. **Variant execution:** Uses `asyncio.create_task` instead of threads
4. **Context propagation:** Context vars work across `await` boundaries

## Error Handling

Exceptions are captured and stored:

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def failing_func(config: Config) -> str:
    raise ValueError("Something went wrong")

try:
    result = failing_func()
except ValueError as e:
    print(f"Caught: {e}")
``````

**Lifecycle behavior:**
1. Primary exception propagates to caller
2. Variant exceptions are captured but don't propagate
3. All exceptions stored in `FunctionResult.exception_info`

## See Also

- [Context Isolation](context-isolation.md) - Deep dive into context management
- [Async Execution Model](async-model.md) - Async-specific details
- [Variant Execution](variant-execution.md) - How variants are executed
