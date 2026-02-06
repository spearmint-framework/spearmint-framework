# Architecture

This document explains how Spearmint is designed and how its components work together.

## High-Level Overview

Spearmint follows a layered architecture:

```
┌─────────────────────────────────────────┐
│          User Function Layer            │  @experiment decorated functions
├─────────────────────────────────────────┤
│       Spearmint API Layer               │  Spearmint class, experiment decorator
├─────────────────────────────────────────┤
│      Experiment Function Layer          │  ExperimentFunction, config binding
├─────────────────────────────────────────┤
│       Execution Runtime Layer           │  ExperimentRunner, context management
├─────────────────────────────────────────┤
│      Configuration Layer                │  Config, DynamicValue, parsing
└─────────────────────────────────────────┘
```

## Core Components

### 1. Spearmint Class (`spearmint.py`)

The main entry point and facade for the framework.

**Responsibilities:**
- Provide decorator API (`@mint.experiment()`)
- Manage default configurations
- Create and return wrapped functions
- Expose static runner methods (`run()`, `arun()`)

**Key Design Decisions:**
- Immutable after initialization
- Thread-safe for concurrent use
- Minimal state (configs, optional strategy)

### 2. ExperimentFunction (`experiment_function.py`)

Wraps user functions with experiment metadata and execution logic.

**Responsibilities:**
- Store function metadata (name, signature)
- Manage function-specific configurations
- Handle type inspection for config binding
- Discover nested experiment calls (via AST parsing)

**Key Features:**
- Lazy initialization of nested experiments
- Pydantic model binding support
- Function signature preservation

### 3. ExperimentRunner (`runner.py`)

Manages experiment execution runtime.

**Responsibilities:**
- Execute experiment functions with proper context
- Handle sync/async execution modes
- Manage variant execution (foreground/background)
- Coordinate context variables

**Execution Flow:**
```python
1. Create ExperimentCase (config mapping)
2. Set context variables
3. Execute main config
4. Execute variant configs (if any)
5. Return ExperimentCaseResults
```

### 4. Configuration System (`configuration/`)

Handles all configuration-related logic.

**Components:**
- `Config`: Dictionary wrapper with Pydantic validation
- `DynamicValue`: Iterator for generating multiple configs
- `generate_configurations()`: Cartesian product expansion
- `parse_configs()`: Unified config parsing

**Configuration Flow:**
```
Input → Parse → Expand → Validate → Inject
```

### 5. Context Management (`context.py`)

Uses Python's `contextvars` to track execution context.

**Context Variables:**
- `experiment_runner`: Current ExperimentRunner instance
- `current_experiment_case`: Current ExperimentCase (config mapping)
- `runtime_context`: Execution metadata

**Benefits:**
- Thread-safe
- Works with async/await
- No global state pollution

### 6. Registry (`registry.py`)

Global registry for experiment functions.

**Purpose:**
- Map function objects to ExperimentFunction instances
- Enable function lookup during nested calls
- Support explicit runner mode

**Current Design:**
```python
experiment_fn_registry = {
    function_object: ExperimentFunction(...)
}
```

## Data Flow

### Decorator Mode (Implicit Execution)

```
User calls function
    ↓
Wrapper checks decorator type (sync/async)
    ↓
Creates context manager (run/arun)
    ↓
ExperimentRunner.run_function()
    ↓
Inject config → Execute → Return result
```

### Runner Mode (Explicit Execution)

```
User creates context (with/async with)
    ↓
Context manager creates ExperimentRunner
    ↓
User calls runner(args)
    ↓
ExperimentRunner.run_function()
    ↓
Returns ExperimentCaseResults with all results
```

## Configuration Injection

### Type-Based Injection

The system inspects function signatures to determine how to inject configs:

```python
@mint.experiment()
def func1(input: str, config: dict) -> str:
    # config injected as dict
    ...

@mint.experiment(bindings={ModelConfig: ""})
def func2(input: str, config: ModelConfig) -> str:
    # config injected as Pydantic model
    ...
```

### Binding Resolution

1. Check experiment bindings for type
2. Extract config subset using binding path
3. Instantiate Pydantic model
4. Inject into function

```python
# Config: {"llm": {"model": "gpt-4", "temp": 0.7}}
# Binding: {ModelConfig: "llm"}
# Result: ModelConfig(model="gpt-4", temp=0.7)
```

## Execution Strategies

### Current: Single Config Strategy

Currently, Spearmint uses a simple execution model:
- First config = main (foreground)
- Remaining configs = variants (background)

```python
configs = [config1, config2, config3]
# config1 → main result (returned)
# config2, config3 → variant results (logged)
```

### Future: Pluggable Strategies

The architecture supports pluggable strategies via the `branch_strategy` parameter:

```python
def my_strategy(
    configs: list[Config],
    ctx: RuntimeContext
) -> tuple[Config, list[Config]]:
    """Select main and variant configs."""
    return main_config, variant_configs
```

Planned strategies:
- **Shadow**: Main foreground, variants background
- **MultiBranch**: All parallel, all returned
- **RoundRobin**: Rotate through configs
- **Adaptive**: Select based on performance

## Sync/Async Handling

Spearmint automatically handles both sync and async functions.

### Detection

Uses `inspect.iscoroutinefunction()` to detect async functions:

```python
if inspect.iscoroutinefunction(func):
    return awrapper  # Async wrapper
else:
    return swrapper  # Sync wrapper
```

### Async in Sync Context

When async functions are called from sync code:

```python
def _run_coroutine_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    
    # If loop exists, run in thread pool
    ctx = contextvars.copy_context()
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(ctx.run, asyncio.run, coro).result()
```

This ensures async experiments work in both sync and async contexts.

## Nested Experiments

Spearmint supports nested experiment calls:

```python
@mint.experiment()
def inner(x: int, config: dict) -> int:
    return x * config['multiplier']

@mint.experiment()
def outer(x: int, config: dict) -> int:
    # Calls inner experiment
    result = inner(x)
    return result + config['offset']
```

### Implementation

1. AST parsing discovers inner calls
2. Register inner experiments during execution
3. Context variables maintain proper config mapping

### Limitations

- Requires source code access (no dynamic functions)
- AST parsing can fail in some environments
- See `.project/tasks/006-ast-source-fragility.md`

## Extension Points

### Custom Config Handlers

Provide custom logic for loading configs from files:

```python
def custom_handler(path: str | Path) -> list[dict[str, Any]]:
    # Load and parse configuration files
    ...

configs = parse_configs(["config.custom"], custom_handler)
```

### Custom Evaluators

Add evaluation logic to experiments:

```python
def accuracy_evaluator(expected: str, trace: dict) -> float:
    actual = trace['data']['spans'][0]['outputs']['output']
    return 1.0 if expected == actual else 0.0

@mint.experiment(evaluators=[accuracy_evaluator])
def process(input: str, config: dict) -> str:
    ...
```

### Custom Branch Strategies

Implement custom config selection logic:

```python
def custom_strategy(
    configs: list[Config],
    ctx: RuntimeContext
) -> tuple[Config, list[Config]]:
    # Custom logic to select main and variants
    main = select_main_config(configs)
    variants = select_variants(configs)
    return main, variants

mint = Spearmint(
    configs=configs,
    branch_strategy=custom_strategy
)
```

## Performance Considerations

### Configuration Expansion

`DynamicValue` creates Cartesian products, which can grow exponentially:

```python
configs = [{
    "a": DynamicValue(range(10)),  # 10 values
    "b": DynamicValue(range(10)),  # 10 values
    "c": DynamicValue(range(10)),  # 10 values
}]
# Creates 10 × 10 × 10 = 1,000 configurations
```

**Recommendation**: Be mindful of configuration explosion.

### Variant Execution

Variants run in background threads/tasks, adding overhead:

```python
# 1 main + 99 variants = 100 parallel executions
configs = [{"id": i} for i in range(100)]
```

**Recommendation**: Limit variant count in production.

### Registry Lookup

Registry uses function object identity for O(1) lookup:

```python
experiment_fn = experiment_fn_registry.get(func)
```

No performance concerns with current design.

## Testing Strategy

### Unit Tests

Test individual components in isolation:
- Configuration parsing
- DynamicValue expansion
- Context management

### Integration Tests

Test component interactions:
- Decorator → Runner → Function execution
- Sync/async handling
- Nested experiments

### Example Tests

Located in `src/tests/test_spearmint.py`.

## Error Handling

### Configuration Errors

- Invalid YAML: Clear error with file path
- Missing bindings: TypeError with expected type
- Invalid DynamicValue: ValueError with details

### Execution Errors

- Function exceptions: Captured in results
- Async errors: Propagated properly
- Context errors: Clear messages

## Future Architecture Changes

See `.project/tasks/` for planned improvements:

1. **Split monolithic module** (001)
2. **Explicit registry lifecycle** (002)
3. **Strategy implementation** (003)
4. **Reduce qualname coupling** (004)
5. **Config binding separation** (007)

## Diagrams

### Component Relationships

```
┌──────────────┐
│   Spearmint  │
└──────┬───────┘
       │ creates
       ↓
┌──────────────────────┐
│ ExperimentFunction   │
└──────┬───────────────┘
       │ registered in
       ↓
┌──────────────────────┐
│      Registry        │
└──────────────────────┘

┌──────────────┐
│     User     │
└──────┬───────┘
       │ calls
       ↓
┌──────────────────────┐
│  ExperimentRunner    │
└──────┬───────────────┘
       │ uses
       ↓
┌──────────────────────┐
│   Configuration      │
└──────────────────────┘
```

### Execution Flow

```
┌─────┐
│Start│
└──┬──┘
   │
   ↓
┌─────────────────────┐
│ Parse Configs       │
└──┬──────────────────┘
   │
   ↓
┌─────────────────────┐
│ Create Wrapper      │
└──┬──────────────────┘
   │
   ↓
┌─────────────────────┐
│ User Calls Function │
└──┬──────────────────┘
   │
   ↓
┌─────────────────────┐
│ Create Runner       │
└──┬──────────────────┘
   │
   ↓
┌─────────────────────┐
│ Inject Config       │
└──┬──────────────────┘
   │
   ↓
┌─────────────────────┐
│ Execute Function    │
└──┬──────────────────┘
   │
   ↓
┌─────────────────────┐
│ Return Results      │
└──┬──────────────────┘
   │
   ↓
┌─────┐
│ End │
└─────┘
```

## See Also

- [Design Decisions](design-decisions.md) - Why things work this way
- [API Reference](../reference/api/spearmint.md) - Public API documentation
- [Contributing](../contributing.md) - Development guidelines
