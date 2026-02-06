# Compare Multiple Configurations

Learn how to run experiments with all configurations and compare results.

## Problem

You want to test multiple configurations (models, parameters, algorithms) and see results from all of them to make informed decisions.

## Solution

Use explicit execution with `Spearmint.run()` or `Spearmint.arun()` to access all results.

## Basic Example

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7},
    {"model": "gpt-3.5-turbo", "temperature": 0.5},
    {"model": "gpt-4-turbo", "temperature": 0.9}
])

@mint.experiment()
def generate_summary(text: str, config: Config) -> str:
    # Your implementation here
    return f"[{config['model']} @ {config['temperature']}] Summary of: {text}"

# Run with all configs
with Spearmint.run(generate_summary, await_variants=True) as runner:
    results = runner("Long article text...")
    
    # Access primary result
    print("PRIMARY:", results.main_result.result)
    
    # Access all variant results
    for variant in results.variant_results:
        print(f"VARIANT [{variant.experiment_case.config.id}]:", variant.result)
``````

**Output:**
``````
PRIMARY: [gpt-4 @ 0.7] Summary of: Long article text...
VARIANT [gpt-3.5-turbo-0.5]: [gpt-3.5-turbo @ 0.5] Summary of: Long article text...
VARIANT [gpt-4-turbo-0.9]: [gpt-4-turbo @ 0.9] Summary of: Long article text...
``````

## Key Points

### 1. Wait for Variants

Use `await_variants=True` to ensure variants complete:

``````python
with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner("input")
    # All variants have finished
``````

**Without `await_variants`:**
``````python
with Spearmint.run(my_function) as runner:  # await_variants defaults to False
    results = runner("input")
    # Variants may still be running in background
    # results.variant_results might be incomplete
``````

### 2. Access Individual Results

Each result contains execution details:

``````python
results = runner("input")

# Main result
main = results.main_result
print(main.result)                       # Return value
print(main.experiment_case.config)       # Config used
print(main.experiment_case.config.id)    # Config ID

# Variant results
for variant in results.variant_results:
    print(variant.result)
    print(variant.experiment_case.config.id)
    if variant.exception_info:
        print(f"Error: {variant.exception_info}")
``````

### 3. Handle Errors

Variants capture exceptions without failing the primary:

``````python
@mint.experiment()
def risky_function(config: Config) -> str:
    if config["model"] == "experimental":
        raise ValueError("Experimental model failed")
    return f"Success with {config['model']}"

with Spearmint.run(risky_function, await_variants=True) as runner:
    results = runner()
    
    # Check variant errors
    for variant in results.variant_results:
        if variant.exception_info:
            print(f"Config {variant.experiment_case.config.id} failed:")
            print(variant.exception_info)
``````

## Comparing Results

### Example: Find Best Configuration

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[
    {"model": "gpt-4", "temp": 0.0},
    {"model": "gpt-4", "temp": 0.5},
    {"model": "gpt-4", "temp": 1.0},
    {"model": "gpt-3.5-turbo", "temp": 0.5}
])

@mint.experiment()
def score_response(question: str, config: Config) -> dict:
    response = generate_with_model(config["model"], config["temp"], question)
    score = evaluate_response(response)  # Your scoring logic
    
    return {
        "response": response,
        "score": score,
        "config": config.id
    }

# Run experiment
with Spearmint.run(score_response, await_variants=True) as runner:
    results = runner("What is machine learning?")
    
    # Collect all results
    all_results = [results.main_result] + results.variant_results
    
    # Find best
    best = max(all_results, key=lambda r: r.result["score"])
    
    print(f"Best config: {best.result['config']}")
    print(f"Score: {best.result['score']}")
    print(f"Response: {best.result['response']}")
``````

### Example: Side-by-Side Comparison

``````python
import pandas as pd

configs = [
    {"model": "gpt-4", "temp": 0.7},
    {"model": "gpt-3.5-turbo", "temp": 0.7},
    {"model": "claude-3", "temp": 0.7}
]

mint = Spearmint(configs=configs)

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return call_model(config["model"], config["temp"], prompt)

# Compare multiple prompts
prompts = [
    "Explain quantum computing",
    "Write a haiku about code",
    "Summarize the water cycle"
]

comparison_data = []

for prompt in prompts:
    with Spearmint.run(generate, await_variants=True) as runner:
        results = runner(prompt)
        
        all_results = [results.main_result] + results.variant_results
        
        for res in all_results:
            comparison_data.append({
                "prompt": prompt[:30],
                "model": res.experiment_case.config["model"],
                "temperature": res.experiment_case.config["temp"],
                "output": res.result[:100]
            })

# Create comparison table
df = pd.DataFrame(comparison_data)
print(df.pivot_table(
    index="prompt",
    columns="model",
    values="output",
    aggfunc="first"
))
``````

## Async Comparison

For async functions, use `Spearmint.arun()`:

``````python
mint = Spearmint(configs=[...])

@mint.experiment()
async def async_generate(prompt: str, config: Config) -> str:
    response = await async_api_call(config["model"], prompt)
    return response.text

async def main():
    async with Spearmint.arun(async_generate, await_variants=True) as runner:
        results = await runner("Test prompt")
        
        print("PRIMARY:", results.main_result.result)
        for variant in results.variant_results:
            print("VARIANT:", variant.result)

import asyncio
asyncio.run(main())
``````

## Batch Processing

Compare configs across a dataset:

``````python
import jsonlines

mint = Spearmint(configs=[...])

@mint.experiment()
def process_item(text: str, config: Config) -> dict:
    result = your_processing(text, config)
    return {"text": text, "result": result, "config": config.id}

# Load dataset
with jsonlines.open("dataset.jsonl") as reader:
    dataset = list(reader)

# Process all items
all_results = []

for item in dataset:
    with Spearmint.run(process_item, await_variants=True) as runner:
        results = runner(item["text"])
        
        # Store all config results for this item
        all_results.extend([results.main_result] + results.variant_results)

# Analyze by config
import pandas as pd
df = pd.DataFrame([{
    "config_id": r.experiment_case.config.id,
    "result": r.result["result"],
    "text": r.result["text"]
} for r in all_results])

print(df.groupby("config_id")["result"].describe())
``````

## Performance Considerations

### Parallel Execution

- **Sync functions:** Variants run in a thread pool (CPU-bound tasks may not benefit)
- **Async functions:** Variants run as concurrent tasks (excellent for I/O-bound tasks)

### Control Parallelism

For many configs, consider custom strategies:

``````python
def limited_parallel_strategy(*args, **kwargs):
    """Only run first 3 configs."""
    all_configs = get_configs()
    return all_configs[0], all_configs[1:3]

mint = Spearmint(
    branch_strategy=limited_parallel_strategy,
    configs=[...100 configs...]
)
``````

## Common Patterns

### Pattern 1: Champion/Challenger

``````python
mint = Spearmint(configs=[
    {"name": "champion", "model": "gpt-4"},
    {"name": "challenger", "model": "gpt-5-beta"}
])

@mint.experiment()
def production_call(query: str, config: Config) -> str:
    return api_call(config["model"], query)

# Champion result returned, challenger logged
result = production_call("user query")
``````

### Pattern 2: A/B/C Testing

``````python
mint = Spearmint(configs=[
    {"variant": "A", "algorithm": "v1"},
    {"variant": "B", "algorithm": "v2"},
    {"variant": "C", "algorithm": "v3"}
])

with Spearmint.run(my_function, await_variants=True) as runner:
    results = runner(input_data)
    
    # Show all variants to user for feedback
    for result in [results.main_result] + results.variant_results:
        display_to_user(result.result, result.experiment_case.config["variant"])
``````

## See Also

- [Use Shadow Testing](shadow-testing.md) - Primary + background variants
- [Run Parameter Sweeps](parameter-sweeps.md) - Generate many configs
- [Experiment Lifecycle](../explanation/experiment-lifecycle.md) - How execution works
