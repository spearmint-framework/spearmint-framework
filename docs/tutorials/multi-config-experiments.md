# Multi-Config Experiments

Learn how to run experiments with multiple configurations simultaneously.

## Overview

When you have multiple configurations to test, Spearmint provides strategies to execute them in different ways:

- **Parallel execution**: Run all configs at once
- **Shadow execution**: Main config + background variants
- **Round-robin**: Rotate through configs

---

## Parallel Execution with MultiBranchStrategy

Run all configurations in parallel and collect results.

### Basic Example

``````python
from spearmint import Spearmint, Config
from spearmint.strategies import MultiBranchStrategy

configs = [
    {"algorithm": "quicksort", "optimization": "standard"},
    {"algorithm": "mergesort", "optimization": "standard"},
    {"algorithm": "heapsort", "optimization": "optimized"},
]

mint = Spearmint(strategy=MultiBranchStrategy, configs=configs)

@mint.experiment()
def sort_data(data: list[int], config: Config) -> tuple[list[int], float]:
    """Sort data and return result + execution time."""
    import time
    start = time.time()
    
    # Select algorithm based on config
    if config['algorithm'] == "quicksort":
        result = sorted(data)  # Python uses Timsort
    # ... other algorithms
    
    duration = time.time() - start
    return result, duration

# Test all configs
with Spearmint.run(sort_data, await_variants=True) as runner:
    data = list(range(1000, 0, -1))  # Reverse sorted
    results = runner(data)
    
    # Compare results
    for branch in [results.main_result] + results.variant_results:
        config = branch.config
        _, duration = branch.result
        print(f"{config['algorithm']}: {duration:.4f}s")
``````

---

## Shadow Testing

Test new configurations in production without impacting users.

### Production Example

``````python
from spearmint.strategies import ShadowStrategy

configs = [
    {"model": "gpt-4", "version": "production"},  # Main
    {"model": "gpt-5", "version": "beta"},         # Shadow
]

mint = Spearmint(strategy=ShadowStrategy, configs=configs)

@mint.experiment()
def generate_response(prompt: str, config: Config) -> str:
    """Generate response with configured model."""
    return call_llm(config['model'], prompt)

# User gets production result immediately
response = generate_response("Hello")
# Beta model runs in background, results logged for comparison
``````

**Benefits:**
- Zero user impact
- Real production data
- Compare performance safely

---

## Dynamic Configuration Generation

Generate many configs programmatically.

### Using DynamicValue

``````python
from spearmint.config import DynamicValue

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo", "claude-3"]),
    "temperature": DynamicValue([0.0, 0.3, 0.7, 1.0]),
    "max_tokens": DynamicValue([100, 250, 500])
}]
# Creates 36 configurations (3 × 4 × 3)
``````

### Using Generators

``````python
def learning_rate_schedule():
    """Generate learning rates on a log scale."""
    for i in range(-5, 0):
        yield 10 ** i

configs = [{
    "learning_rate": DynamicValue(learning_rate_schedule()),
    "batch_size": DynamicValue([32, 64, 128])
}]
``````

---

## Comparing Results

### Structured Comparison

``````python
@mint.experiment()
def evaluate(text: str, config: Config) -> dict:
    """Return structured evaluation results."""
    result = process_with_config(text, config)
    return {
        "output": result,
        "tokens": count_tokens(result),
        "quality_score": evaluate_quality(result)
    }

with Spearmint.run(evaluate, await_variants=True) as runner:
    results = runner("Test input")
    
    # Create comparison table
    comparison = []
    for branch in [results.main_result] + results.variant_results:
        comparison.append({
            "config": branch.config['model'],
            "tokens": branch.result['tokens'],
            "quality": branch.result['quality_score']
        })
    
    # Display as table
    import pandas as pd
    df = pd.DataFrame(comparison)
    print(df.to_string())
``````

---

## Best Practices

### 1. Start Small

Begin with 2-3 configs, then expand:

``````python
# ✅ Start here
configs = [
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"}
]

# Later expand to
configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo", "claude-3"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0])
}]
``````

### 2. Use Meaningful Config IDs

``````python
configs = [
    {"model": "gpt-4", "__config_id__": "prod-stable"},
    {"model": "gpt-5", "__config_id__": "test-beta"}
]
``````

### 3. Monitor Resource Usage

``````python
import psutil

@mint.experiment()
def resource_intensive_task(data: str, config: Config) -> dict:
    start_memory = psutil.Process().memory_info().rss
    
    result = process(data, config)
    
    end_memory = psutil.Process().memory_info().rss
    memory_used = (end_memory - start_memory) / 1024 / 1024  # MB
    
    return {
        "result": result,
        "memory_mb": memory_used
    }
``````

---

## See Also

- [Strategies Reference](../reference/strategies.md)
- [Configuration System](../reference/configuration.md)
- [Testing Experiments](../how-to/testing-experiments.md)
