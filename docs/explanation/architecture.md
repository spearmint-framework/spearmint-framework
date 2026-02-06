# Architecture Overview

This document explains how Spearmint works internally, helping you understand the framework's design and implementation.

## High-Level Architecture

Spearmint follows a **decorator + registry** pattern with **context-aware execution**:

``````
┌─────────────────────────────────────────────────────────┐
│                    @experiment Decorator                 │
│  • Wraps user function                                  │
│  • Registers in global registry                         │
│  • Performs AST analysis for nested calls               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              ExperimentFunction                          │
│  • Stores function metadata                             │
│  • Manages config bindings                              │
│  • Handles parameter injection                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                  Strategy Selection                      │
│  • Chooses main config + variants                       │
│  • SingleConfigStrategy (default)                       │
│  • MultiBranchStrategy, ShadowStrategy, etc.            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│               ExperimentRunner                           │
│  • Executes main config synchronously                   │
│  • Spawns variants in background                        │
│  • Manages threading/async tasks                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│               RuntimeContext                             │
│  • Per-execution context variables                      │
│  • Async-safe state management                          │
│  • Config ID tracking                                   │
└─────────────────────────────────────────────────────────┘
``````

---

## Core Components

### 1. Decorator & Registration

When you use `@mint.experiment()`, Spearmint:

1. **Wraps the function** with experiment logic
2. **Performs AST analysis** to discover nested function calls
3. **Registers** the function in `ExperimentFunctionRegistry`
4. **Creates** an `ExperimentFunction` object with metadata

**Example:**
``````python
@mint.experiment()
def my_func(prompt: str, config: Config) -> str:
    return helper_func(prompt, config)  # Detected via AST
``````

The AST analysis allows Spearmint to propagate configurations to nested experiment functions automatically.

---

### 2. Configuration System

Spearmint's configuration system has three layers:

#### Layer 1: Parsing
``````python
parse_configs([
    {"model": "gpt-4"},        # Dict
    "config.yaml",              # File
    "configs/",                 # Directory
])
``````

Converts various sources into standardized `dict` format.

#### Layer 2: Expansion
``````python
from spearmint.config import DynamicValue

config = {
    "model": DynamicValue(["gpt-4", "gpt-3.5"]),
    "temp": DynamicValue([0.0, 0.5])
}
# Expands to 4 configs via cartesian product
``````

`generate_configurations()` creates all combinations of `DynamicValue` fields.

#### Layer 3: Binding
``````python
from typing import Annotated
from spearmint.config import Bind

@mint.experiment()
def func(config: Annotated[ModelConfig, Bind("llm.model")]) -> str:
    pass
``````

Maps configuration paths to typed Pydantic models for type safety and IDE support.

---

### 3. Strategy Pattern

Strategies control *how* configurations are executed:

``````python
def strategy(configs: list[dict]) -> tuple[dict, list[dict]]:
    """
    Args:
        configs: All available configurations
    
    Returns:
        (main_config, variant_configs)
    """
    main = configs[0]
    variants = configs[1:]
    return main, variants
``````

**Built-in strategies:**

| Strategy | Behavior |
|----------|----------|
| **SingleConfigStrategy** | Runs first config only, no variants |
| **ShadowStrategy** | Main config in foreground, variants in background |
| **MultiBranchStrategy** | All configs in parallel, returns all results |
| **RoundRobinStrategy** | Cycles through configs on each call |

**Custom strategies:**
``````python
def my_strategy(configs):
    # Custom selection logic
    main = select_best_config(configs)
    variants = [c for c in configs if c != main]
    return main, variants

mint = Spearmint(strategy=my_strategy, configs=configs)
``````

---

### 4. Execution Model

#### Direct Call Pattern

``````python
@mint.experiment()
def process(text: str, config: Config) -> str:
    return f"{config['model']}: {text}"

result = process("hello")  # Direct call
``````

**Flow:**
1. Wrapper intercepts the call
2. Strategy selects main + variants
3. Main config executes synchronously
4. Variants spawn in background threads (daemon mode)
5. Result from main config returned immediately

#### Context Manager Pattern

``````python
with Spearmint.run(process) as runner:
    result = runner("hello")
``````

**Flow:**
1. Context manager creates `ExperimentRunner`
2. Runner executes with strategy
3. Optionally waits for variants (`await_variants=True`)
4. Returns structured result object

---

### 5. Context Management

Spearmint uses Python's `contextvars` for thread-safe and async-safe state:

``````python
from spearmint.context import RuntimeContext, experiment_case_var

# Set context for current execution
with RuntimeContext(experiment_case):
    # All code here has access to experiment_case
    current_case = experiment_case_var.get()
``````

**Why contextvars?**
- **Thread-safe**: Each thread has isolated context
- **Async-safe**: Works across async/await boundaries
- **Clean**: No global mutable state

**Use cases:**
- Tracking current config ID during execution
- Propagating experiment metadata to nested functions
- MLflow trace integration

---

### 6. AST-Based Function Discovery

Spearmint uses Python's `ast` module to detect nested function calls:

``````python
@mint.experiment()
def parent_func(text: str, config: Config) -> str:
    # Spearmint detects this call via AST
    result = child_func(text, config)
    return result

@mint.experiment()
def child_func(text: str, config: Config) -> str:
    return f"{config['model']}: {text}"
``````

**How it works:**
1. Parse function source code with `ast.parse()`
2. Walk AST to find `Call` nodes
3. Match call names against registered experiments
4. Auto-inject config parameters when calling nested experiments

**Benefits:**
- Automatic config propagation
- No manual config passing needed
- Type-safe parameter binding

**Limitations:**
- Requires source code access (fails with bytecode-only modules)
- Dynamic function calls (via variables) not detected

---

## Concurrency Model

### Synchronous Execution

``````python
@mint.experiment()
def sync_func(text: str, config: Config) -> str:
    return f"Result: {text}"

result = sync_func("hello")
``````

**Threading:**
- Main config: Runs in calling thread
- Variants: Run in `ThreadPoolExecutor` (daemon threads)
- Variants don't block return

### Asynchronous Execution

``````python
@mint.experiment()
async def async_func(text: str, config: Config) -> str:
    await asyncio.sleep(0.1)
    return f"Result: {text}"

result = await async_func("hello")
``````

**Async tasks:**
- Main config: Runs in current event loop
- Variants: Run as background tasks (`asyncio.create_task`)
- Variants don't block return

---

## Configuration ID Generation

Each configuration gets a unique ID via SHA256 hashing:

``````python
import hashlib
import json

def generate_config_id(config: dict) -> str:
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]
``````

**Custom IDs:**
``````python
config = {
    "model": "gpt-4",
    "__config_id__": "my-custom-id"  # Override
}
``````

---

## MLflow Integration

Spearmint integrates with MLflow for tracing:

``````python
import mlflow

# Automatic trace logging for decorated functions
@mint.experiment()
def my_func(text: str, config: Config) -> str:
    # Execution automatically logged to MLflow traces
    return f"Result: {text}"

# Query traces
traces = mlflow.search_traces()
``````

**Trace includes:**
- Function name and parameters
- Configuration used
- Execution duration
- Result or exception
- Config ID for correlation

---

## Error Handling

### Variant Failures

Variants run in background and **don't propagate exceptions** to main thread:

``````python
@mint.experiment()
def risky_func(text: str, config: Config) -> str:
    if config['model'] == "bad-model":
        raise ValueError("Invalid model")
    return f"Result: {text}"

# Main config succeeds, variant failure is logged but doesn't crash
result = risky_func("hello")
``````

**Exception callback:**
``````python
def handle_variant_error(exception: Exception):
    logger.error(f"Variant failed: {exception}")

# Variants use callback for exception handling
``````

### Main Config Failures

Main config exceptions **propagate normally**:

``````python
try:
    result = my_func("input")
except ValueError as e:
    # Handle main config failure
    pass
``````

---

## Performance Considerations

### Memory

- **Config copies**: Each variant gets a deep copy of config
- **Context vars**: Minimal overhead per execution
- **Registry**: Stores metadata for all decorated functions (small footprint)

### CPU

- **AST parsing**: One-time cost at decoration (negligible)
- **Threading**: Variants run in parallel on multi-core systems
- **Config hashing**: Fast (SHA256 on small JSON strings)

### I/O

- **MLflow traces**: Async logging (non-blocking)
- **YAML/JSONL loading**: Lazy loading supported
- **File watchers**: Not implemented (configs loaded once)

---

## Design Principles

1. **Minimal invasiveness**: Decorator pattern doesn't change function signatures
2. **Type safety**: Pydantic models + `Annotated` for IDE support
3. **Async-first**: Built with async/await in mind from day one
4. **Extensibility**: Strategy pattern allows custom execution logic
5. **Observability**: MLflow integration for tracing and evaluation
6. **Developer experience**: Clear errors, intuitive APIs, comprehensive docs

---

## Comparison to Alternatives

### vs. Hydra
- **Spearmint**: Runtime config injection, ideal for online experiments
- **Hydra**: CLI-based config management, better for offline batch jobs

### vs. LaunchDarkly
- **Spearmint**: Open-source, self-hosted, code-first
- **LaunchDarkly**: SaaS feature flags, UI-driven, enterprise features

### vs. Manual Parameter Passing
- **Spearmint**: Automatic config propagation, tracing, multi-variant support
- **Manual**: Full control, no dependencies, more boilerplate

---

## See Also

- [Design Decisions](design-decisions.md) - Why we made specific choices
- [API Reference](../reference/api.md) - Complete API docs
- [Strategies](../reference/strategies.md) - Available execution strategies
