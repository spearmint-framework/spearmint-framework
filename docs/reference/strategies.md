# Strategies

Execution strategies control how Spearmint runs your configurations.

## Overview

A **strategy** is a function that selects which configuration is the "main" config and which are "variants":

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

---

## Built-in Strategies

### SingleConfigStrategy (Default)

Runs only the first configuration. No variants execute.

``````python
from spearmint import Spearmint

configs = [
    {"model": "gpt-4"},
    {"model": "gpt-3.5"},  # Won't run
]

mint = Spearmint(configs=configs)
# Uses SingleConfigStrategy by default
``````

**Use when:**
- You want simple, single-config execution
- Testing a specific configuration
- Production with one approved config

---

### ShadowStrategy

Main config runs in foreground, variants in background for comparison.

``````python
from spearmint import Spearmint
from spearmint.strategies import ShadowStrategy

configs = [
    {"model": "gpt-4"},        # Main (production)
    {"model": "gpt-5-beta"},   # Shadow (testing)
]

mint = Spearmint(strategy=ShadowStrategy, configs=configs)

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return call_llm(config['model'], prompt)

result = generate("Hello")  # Returns gpt-4 result immediately
# gpt-5-beta runs in background, logged for comparison
``````

**Use when:**
- Testing new models/algorithms in production
- Comparing performance without blocking users
- Gradual rollout of new features

**Characteristics:**
- Main result returned immediately
- Variants run in daemon threads (don't block)
- Variant failures don't crash main execution

---

### MultiBranchStrategy

Runs all configurations in parallel, returns all results.

``````python
from spearmint import Spearmint
from spearmint.strategies import MultiBranchStrategy

configs = [
    {"model": "gpt-4", "temperature": 0.0},
    {"model": "gpt-4", "temperature": 0.5},
    {"model": "gpt-3.5-turbo", "temperature": 0.0},
]

mint = Spearmint(strategy=MultiBranchStrategy, configs=configs)

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return call_llm(config['model'], config['temperature'], prompt)

with Spearmint.run(generate, await_variants=True) as runner:
    results = runner("Hello")
    
    print(f"Main: {results.main_result.result}")
    for variant in results.variant_results:
        print(f"Variant: {variant.result}")
``````

**Use when:**
- A/B/n testing with user feedback
- Comparing multiple algorithms
- Offline batch evaluation

**Characteristics:**
- All configs run in parallel
- Must use `await_variants=True` to get all results
- First config is "main", rest are "variants"

---

### RoundRobinStrategy

Cycles through configurations on each call.

``````python
from spearmint import Spearmint
from spearmint.strategies import RoundRobinStrategy

configs = [
    {"model": "gpt-4"},
    {"model": "gpt-3.5-turbo"},
    {"model": "claude-3"},
]

mint = Spearmint(strategy=RoundRobinStrategy, configs=configs)

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return call_llm(config['model'], prompt)

result1 = generate("Hello")  # Uses gpt-4
result2 = generate("World")  # Uses gpt-3.5-turbo
result3 = generate("!")      # Uses claude-3
result4 = generate("Again")  # Back to gpt-4
``````

**Use when:**
- Load balancing across multiple backends
- Rotating through rate-limited APIs
- Fair distribution of traffic

**Characteristics:**
- Maintains internal state (call count)
- Thread-safe counter
- Cycles indefinitely

---

## Custom Strategies

### Simple Custom Strategy

``````python
def newest_first_strategy(configs: list[dict]) -> tuple[dict, list[dict]]:
    """Use the newest config as main."""
    main = configs[-1]  # Last config
    variants = configs[:-1]
    return main, variants

mint = Spearmint(strategy=newest_first_strategy, configs=configs)
``````

### Weighted Random Strategy

``````python
import random

def weighted_strategy(configs: list[dict]) -> tuple[dict, list[dict]]:
    """Select main config based on weights."""
    weights = [c.get('weight', 1.0) for c in configs]
    main = random.choices(configs, weights=weights, k=1)[0]
    variants = [c for c in configs if c != main]
    return main, variants

configs = [
    {"model": "gpt-4", "weight": 0.8},
    {"model": "gpt-3.5", "weight": 0.2},
]

mint = Spearmint(strategy=weighted_strategy, configs=configs)
``````

### Performance-Based Strategy

``````python
import time

class PerformanceStrategy:
    def __init__(self):
        self.performance = {}
    
    def __call__(self, configs: list[dict]) -> tuple[dict, list[dict]]:
        """Select fastest config as main."""
        if not self.performance:
            # First call: use first config
            return configs[0], configs[1:]
        
        # Select config with best (lowest) avg time
        best_config = min(
            configs,
            key=lambda c: self.performance.get(c['id'], float('inf'))
        )
        variants = [c for c in configs if c != best_config]
        return best_config, variants
    
    def record(self, config_id: str, duration: float):
        """Record execution time."""
        if config_id not in self.performance:
            self.performance[config_id] = []
        self.performance[config_id].append(duration)

perf_strategy = PerformanceStrategy()
mint = Spearmint(strategy=perf_strategy, configs=configs)
``````

### Canary Release Strategy

``````python
def canary_strategy(canary_percent: float = 0.1):
    """Route small percentage of traffic to canary config."""
    import random
    
    def strategy(configs: list[dict]) -> tuple[dict, list[dict]]:
        production = configs[0]
        canary = configs[1] if len(configs) > 1 else production
        
        # Route canary_percent% to canary config
        if random.random() < canary_percent:
            return canary, [production]
        else:
            return production, [canary]
    
    return strategy

mint = Spearmint(
    strategy=canary_strategy(canary_percent=0.1),  # 10% to canary
    configs=[
        {"model": "gpt-4", "version": "stable"},
        {"model": "gpt-4", "version": "canary"},
    ]
)
``````

---

## Strategy Overrides

### Override at Decorator Level

``````python
mint = Spearmint(configs=configs)  # Default strategy

@mint.experiment(strategy=MultiBranchStrategy)
def compare_all(prompt: str, config: Config) -> str:
    # This function uses MultiBranchStrategy
    return call_llm(config['model'], prompt)

@mint.experiment()  # Uses default strategy
def use_single(prompt: str, config: Config) -> str:
    return call_llm(config['model'], prompt)
``````

---

## Best Practices

### 1. Match Strategy to Use Case

| Use Case | Recommended Strategy |
|----------|---------------------|
| Production single config | SingleConfigStrategy |
| Testing new models | ShadowStrategy |
| A/B testing | MultiBranchStrategy |
| Load balancing | RoundRobinStrategy |
| Gradual rollout | Custom canary strategy |

### 2. Handle Variant Failures Gracefully

``````python
@mint.experiment()
def robust_call(prompt: str, config: Config) -> str:
    try:
        return call_llm(config['model'], prompt)
    except Exception as e:
        logger.error(f"Config {config['model']} failed: {e}")
        raise  # Re-raise for main config, logged for variants
``````

### 3. Monitor All Configs

Use MLflow or similar tools to track:
- Execution times
- Success rates
- Output quality
- Resource usage

### 4. Test Strategies

``````python
def test_shadow_strategy():
    """Ensure shadow strategy works correctly."""
    configs = [{"id": "main"}, {"id": "shadow"}]
    
    def shadow_strategy(configs):
        return configs[0], configs[1:]
    
    main, variants = shadow_strategy(configs)
    
    assert main['id'] == "main"
    assert len(variants) == 1
    assert variants[0]['id'] == "shadow"
``````

---

## Performance Considerations

### Threading vs Async

**Sync functions:**
``````python
@mint.experiment()
def sync_func(config: Config) -> str:
    # Variants run in ThreadPoolExecutor
    return "result"
``````

**Async functions:**
``````python
@mint.experiment()
async def async_func(config: Config) -> str:
    # Variants run as asyncio tasks
    return "result"
``````

### Resource Limits

Limit concurrent variants:

``````python
from concurrent.futures import ThreadPoolExecutor

# Custom executor with max workers
executor = ThreadPoolExecutor(max_workers=3)

# Use in your runner (implementation-specific)
``````

---

## See Also

- [API Reference](api.md) - Complete API documentation
- [Architecture](../explanation/architecture.md) - How strategies work internally
- [Configuration System](configuration.md) - Config management
