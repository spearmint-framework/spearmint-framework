# Quick Start

Get started with Spearmint in 5 minutes.

## Your First Experiment

Let's create a simple experiment that compares two LLM configurations:

```python
from spearmint import Spearmint

# 1. Create a Spearmint instance with configurations
mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7},
])

# 2. Decorate your function
@mint.experiment()
def generate_text(prompt: str, config: dict) -> str:
    # config is automatically injected
    model = config["model"]
    temp = config["temperature"]
    return f"Using {model} at temp {temp}: {prompt}"

# 3. Call your function normally
result = generate_text("Hello, Spearmint!")
print(result)
# Output: "Using gpt-4 at temp 0.7: Hello, Spearmint!"
```

That's it! Spearmint handles configuration injection automatically.

## Comparing Multiple Configurations

Now let's compare multiple configurations side by side. We'll use the explicit runner API to see all results:

```python
from spearmint import Spearmint

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.0},
    {"model": "gpt-4", "temperature": 0.5},
    {"model": "gpt-3.5-turbo", "temperature": 0.7},
])

@mint.experiment()
def generate_summary(text: str, config: dict) -> str:
    # Your actual LLM call would go here
    return f"Summary using {config['model']} (temp={config['temperature']})"

# Run the experiment explicitly to see all results
with Spearmint.run(generate_summary) as runner:
    results = runner("Long article text...")
    
    # Access the main result (first config)
    print("Main result:", results.main_result.result)
    
    # Access variant results (other configs)
    for variant in results.variant_results:
        print(f"Variant result: {variant.result}")
```

## Using Dynamic Configurations

Generate multiple configurations from parameter ranges:

```python
from spearmint import Spearmint
from spearmint.configuration import DynamicValue

mint = Spearmint(configs=[{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0])
}])
# This creates 6 configurations (2 models × 3 temperatures)

@mint.experiment()
def generate(prompt: str, config: dict) -> str:
    return f"{config['model']}: {prompt}"

result = generate("Test prompt")
print(result)
```

## Working with Async Functions

Spearmint automatically handles async functions:

```python
import asyncio
from spearmint import Spearmint

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
async def async_generate(prompt: str, config: dict) -> str:
    # Your async operation here
    await asyncio.sleep(0.1)
    return f"{config['model']}: {prompt}"

# Call async functions normally with await
async def main():
    result = await async_generate("Hello async!")
    print(result)

asyncio.run(main())
```

## Using Typed Configurations

Use Pydantic models for type-safe configurations:

```python
from pydantic import BaseModel
from spearmint import Spearmint

class LLMConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int = 1000

mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7}
])

# Bind the typed model to the config
@mint.experiment(bindings={LLMConfig: ""})
def generate(prompt: str, config: LLMConfig) -> str:
    # config is now a typed LLMConfig with IDE support
    return f"{config.model}: {prompt}"

result = generate("Type-safe prompt")
```

## Loading Configurations from Files

Load configurations from YAML files:

```yaml
# config.yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
```

```python
from spearmint import Spearmint

# Load a single config file
mint = Spearmint(configs=["config.yaml"])

# Or load all YAML files from a directory
mint = Spearmint(configs=["configs/"])

@mint.experiment()
def generate(prompt: str, config: dict) -> str:
    return f"{config['model']}: {prompt}"
```

## What's Next?

Now that you've built your first experiments, explore:

- **[Core Concepts](concepts.md)** - Understand configurations, strategies, and experiments in depth
- **[How-To Guides](../how-to/configurations.md)** - Learn specific techniques
- **[Cookbook](../../cookbook/README.md)** - Explore more examples
- **[API Reference](../reference/api/spearmint.md)** - Detailed API documentation

## Common Patterns

### Pattern 1: Shadow Testing in Production

Test new configurations without affecting production traffic:

```python
from spearmint import Spearmint

mint = Spearmint(configs=[
    {"model": "gpt-4"},        # Primary (index 0)
    {"model": "gpt-5-beta"},   # Shadow
])

@mint.experiment()
def api_handler(query: str, config: dict) -> str:
    # Primary runs synchronously and returns
    # Shadow runs in background for logging
    return call_llm(config['model'], query)
```

### Pattern 2: Dataset Evaluation

Run experiments on entire datasets:

```python
from spearmint import Spearmint

mint = Spearmint(configs=[{"algorithm": "v1"}])

@mint.experiment()
def process_item(input_text: str, config: dict) -> str:
    return f"{config['algorithm']}: {input_text}"

# Process dataset entries
with Spearmint.run(process_item) as runner:
    results = runner("data entry")
```

## Troubleshooting

### Config Not Injected

Make sure you're using the `@mint.experiment()` decorator and accepting a `config` parameter:

```python
@mint.experiment()  # Don't forget the ()
def my_function(prompt: str, config: dict) -> str:  # config parameter required
    return f"{config['model']}: {prompt}"
```

### Import Errors

Verify Spearmint is installed:

```bash
pip list | grep spearmint-framework
```

### Type Hints Not Working

Ensure your IDE supports Pydantic type hints and you've imported the correct types:

```python
from spearmint import Spearmint
from spearmint.configuration import Config
```

Need more help? Check the [API Reference](../reference/api/spearmint.md) or [open an issue](https://github.com/spearmint-framework/spearmint-framework/issues).
