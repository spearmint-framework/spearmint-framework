# Getting Started with Spearmint

Learn the fundamentals by creating your first experiment.

## What You'll Build

A text generation function that tests multiple AI model configurations to find the best one for your use case.

## Prerequisites

- Python 3.10 or higher
- Basic Python knowledge
- 15 minutes

## Step 1: Install Spearmint

``````bash
pip install spearmint-framework
``````

## Step 2: Create Your First Experiment

Create a file called `first_experiment.py`:

``````python
from spearmint import Spearmint, Config

# Initialize Spearmint with a single configuration
mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7}
])

# Decorate your function
@mint.experiment()
def generate_summary(text: str, config: Config) -> str:
    """Generate a summary using the configured model."""
    # In a real application, you'd call an AI API here
    model = config["model"]
    temp = config["temperature"]
    return f"[{model} @ temp={temp}] Summary of: {text[:50]}..."

# Call the function normally
result = generate_summary("Long article text here...")
print(result)
``````

**Run it:**

``````bash
python first_experiment.py
``````

**Output:**
``````
[gpt-4 @ temp=0.7] Summary of: Long article text here...
``````

### What Just Happened?

1. **Spearmint initialization:** Created a Spearmint instance with one configuration
2. **Decorator application:** Wrapped the function with `@mint.experiment()`
3. **Automatic injection:** Spearmint injected the `config` parameter
4. **Normal execution:** Called the function like any Python function

## Step 3: Compare Multiple Configurations

Now let's test multiple models to see which performs best:

``````python
from spearmint import Spearmint, Config

# Multiple configurations to test
mint = Spearmint(configs=[
    {"model": "gpt-4", "temperature": 0.7},
    {"model": "gpt-3.5-turbo", "temperature": 0.5},
    {"model": "gpt-4-turbo", "temperature": 0.9},
])

@mint.experiment()
def generate_summary(text: str, config: Config) -> str:
    model = config["model"]
    temp = config["temperature"]
    return f"[{model} @ temp={temp}] Summary of: {text[:50]}..."

# By default, only the first config runs
result = generate_summary("Article about AI...")
print(result)
``````

**Output:**
``````
[gpt-4 @ temp=0.7] Summary of: Article about AI...
``````

### Default Behavior

By default, Spearmint uses the **first configuration** as the primary. Other configs become "variants" for comparison (we'll explore this in the next tutorial).

## Step 4: Use Explicit Execution

For more control, use the runner context managers:

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4", "temperature": 0.7}])

@mint.experiment()
def generate_summary(text: str, config: Config) -> str:
    return f"Summary using {config['model']}"

# Explicit sync execution
with Spearmint.run(generate_summary) as runner:
    results = runner("Article text...")
    print(f"Result: {results.main_result.result}")
    print(f"Config ID: {results.main_result.experiment_case.config.id}")
``````

**Output:**
``````
Result: Summary using gpt-4
Config ID: gpt-4-0.7
``````

### When to Use Explicit Execution?

- **Testing:** Better control for assertions and result inspection
- **Batch processing:** Run the same experiment on multiple inputs
- **Custom logic:** Access detailed results and metadata

## Step 5: Async Support

Spearmint supports async functions natively:

``````python
import asyncio
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
async def fetch_and_summarize(url: str, config: Config) -> str:
    # Simulated async API call
    await asyncio.sleep(0.1)
    return f"Summary from {url} using {config['model']}"

# Async execution
async def main():
    result = await fetch_and_summarize("https://example.com")
    print(result)

asyncio.run(main())
``````

## What You Learned

✅ Install and import Spearmint  
✅ Create experiments with `@mint.experiment()`  
✅ Define configurations as dictionaries  
✅ Access injected `Config` objects  
✅ Use explicit execution with `Spearmint.run()`  
✅ Work with async functions  

## Next Steps

- **[Configuration Basics](configuration-basics.md):** Learn YAML configs, dynamic values, and type safety
- **[How-To: Compare Configurations](../how-to/compare-configurations.md):** Use all configs in parallel
- **[Explanation: Experiment Lifecycle](../explanation/experiment-lifecycle.md):** Understand what happens under the hood

## Common Questions

### Can I use Spearmint without the decorator?

Yes! Use `Spearmint.run()` or `Spearmint.arun()` with any function:

``````python
from spearmint import Spearmint, Config

def my_function(prompt: str, config: Config) -> str:
    return f"Output with {config}"

mint = Spearmint(configs=[{"model": "gpt-4"}])

with mint.run(my_function) as runner:
    result = runner("test")
``````

### What if I don't need experiments?

Don't use Spearmint! For simple parameter passing, use regular function arguments. Spearmint adds overhead and is designed for comparing multiple configurations.

### Can I change configurations at runtime?

Yes, pass `configs` to the decorator:

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment(configs=[{"new": "config"}])
def my_function(config: Config) -> str:
    return config["new"]
``````
