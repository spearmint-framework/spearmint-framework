# Getting Started with Spearmint

Welcome! This tutorial will guide you through your first steps with Spearmint, an experiment framework for testing multiple configurations of your code.

## What You'll Learn

- How to install Spearmint
- Basic concepts (configs, decorators, experiments)
- Running your first experiment
- Understanding results

**Time estimate:** 10 minutes

---

## Prerequisites

- Python 3.10 or higher
- Basic understanding of Python functions and decorators
- Familiarity with dictionaries

---

## Installation

Install Spearmint using pip:

``````bash
pip install spearmint-framework
``````

Or with uv:

``````bash
uv add spearmint-framework
``````

Verify installation:

``````python
import spearmint
print(spearmint.__version__)
``````

---

## Core Concepts

Before diving in, let's understand three key concepts:

### 1. Configuration

A **configuration** is a set of parameters you want to test:

``````python
config = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
}
``````

### 2. Experiment

An **experiment** is a function decorated with `@experiment` that receives a config:

``````python
@mint.experiment()
def my_function(input: str, config: Config) -> str:
    # Use config parameters here
    return f"Processed with {config['model']}: {input}"
``````

### 3. Strategy

A **strategy** controls how configurations are executed:
- **Single**: Run one config
- **Shadow**: Run main config + variants in background
- **MultiBranch**: Run all configs in parallel

---

## Your First Experiment

Let's create a simple experiment that tests different greeting styles.

### Step 1: Import Spearmint

``````python
from spearmint import Spearmint, Config
``````

### Step 2: Define Configurations

``````python
configs = [
    {"style": "formal", "greeting": "Good day"},
    {"style": "casual", "greeting": "Hey"},
    {"style": "friendly", "greeting": "Hello"},
]
``````

### Step 3: Initialize Spearmint

``````python
mint = Spearmint(configs=configs)
``````

### Step 4: Create an Experiment Function

``````python
@mint.experiment()
def greet_user(name: str, config: Config) -> str:
    """Generate a greeting based on configuration."""
    style = config['style']
    greeting = config['greeting']
    return f"{greeting}, {name}! (Style: {style})"
``````

### Step 5: Run the Experiment

``````python
result = greet_user("Alice")
print(result)
# Output: "Good day, Alice! (Style: formal)"
``````

**Note:** By default, only the first config runs. Later, we'll explore multi-config execution.

---

## Complete Example

Here's the complete code:

``````python
from spearmint import Spearmint, Config

# Define configurations
configs = [
    {"style": "formal", "greeting": "Good day"},
    {"style": "casual", "greeting": "Hey"},
    {"style": "friendly", "greeting": "Hello"},
]

# Initialize Spearmint
mint = Spearmint(configs=configs)

# Create experiment function
@mint.experiment()
def greet_user(name: str, config: Config) -> str:
    """Generate a greeting based on configuration."""
    style = config['style']
    greeting = config['greeting']
    return f"{greeting}, {name}! (Style: {style})"

# Run experiment
if __name__ == "__main__":
    result = greet_user("Alice")
    print(result)
``````

Run it:

``````bash
python my_experiment.py
``````

---

## Understanding What Happened

When you called `greet_user("Alice")`:

1. **Decorator intercepts**: The `@experiment` decorator catches the call
2. **Strategy selects config**: Default strategy chooses first config (`formal`)
3. **Config injected**: Spearmint adds `config` parameter automatically
4. **Function executes**: Your code runs with the config values
5. **Result returned**: Output is returned to caller

---

## Testing Different Configs

To test a different config, reorder the list:

``````python
configs = [
    {"style": "casual", "greeting": "Hey"},      # Now first (will run)
    {"style": "formal", "greeting": "Good day"},
    {"style": "friendly", "greeting": "Hello"},
]

result = greet_user("Bob")
print(result)
# Output: "Hey, Bob! (Style: casual)"
``````

---

## Using Context Managers

For more control, use context managers:

``````python
with Spearmint.run(greet_user) as runner:
    result = runner("Charlie")
    print(result.main_result.result)
``````

**Benefits:**
- Access to structured result objects
- Ability to wait for variant results
- Better for testing and debugging

---

## Next Steps

Congratulations! You've created your first Spearmint experiment. 

**Continue learning:**
- [Your First Real Experiment](your-first-experiment.md) - Build a practical LLM experiment
- [Multi-Config Experiments](multi-config-experiments.md) - Run multiple configs in parallel
- [Cookbook](../../cookbook/) - Practical examples

**Explore features:**
- [Configuration System](../reference/configuration.md) - Advanced config options
- [Strategies](../reference/strategies.md) - Different execution strategies
- [API Reference](../reference/api.md) - Complete API documentation

---

## Common Questions

### Q: Do I need to add `config` to my function signature?

**A:** Yes. Spearmint injects the config, but your function must accept it:

``````python
# ✅ Correct
@mint.experiment()
def my_func(input: str, config: Config) -> str:
    pass

# ❌ Wrong - missing config parameter
@mint.experiment()
def my_func(input: str) -> str:
    pass
``````

### Q: Can I use type hints?

**A:** Yes! Type hints work normally:

``````python
@mint.experiment()
def my_func(input: str, config: Config) -> str:
    return f"{config['model']}: {input}"
``````

### Q: What if I want multiple configs to run?

**A:** Use a different strategy. See [Multi-Config Experiments](multi-config-experiments.md).

---

## Troubleshooting

### Import Error

``````
ImportError: No module named 'spearmint'
``````

**Solution:** Ensure Spearmint is installed: `pip install spearmint-framework`

### Missing Config Parameter

``````
TypeError: my_func() missing 1 required positional argument: 'config'
``````

**Solution:** Add `config: Config` parameter to your function signature.

### Config Key Error

``````
KeyError: 'model'
``````

**Solution:** Ensure your config dict contains the key you're accessing:

``````python
config = {"model": "gpt-4"}  # ✅ Has 'model' key
result = config['model']
``````

---

## Summary

You learned:
- ✅ How to install Spearmint
- ✅ Core concepts (config, experiment, strategy)
- ✅ How to create and run experiments
- ✅ Using context managers for structured results

**Next:** [Your First Real Experiment](your-first-experiment.md)
