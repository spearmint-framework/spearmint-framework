# Spearmint 🌱

An experiment framework for testing multiple configurations of your code in parallel or sequentially. Think of it as A/B testing for your functions.

## What is Spearmint?

Spearmint helps you answer questions like:
- "Which model performs better: GPT-4 or GPT-3.5?"
- "What temperature value gives the best results?"
- "How does this new algorithm compare to the old one?"

Instead of manually running your code with different parameters and tracking results, Spearmint automates this process using **strategies** and **configurations**.

> If you learn better by seeing code in action, check out the [examples directory](samples/).

## Core Concepts

### 1. Configurations
A configuration is a set of parameters you want to test. You can define them as:
- Python dictionaries: `{"model": "gpt-4", "temperature": 0.5}`
- YAML files: `config.yaml`
- Pydantic models: Custom typed configuration classes

### 2. Strategies
Strategies control *how* your configurations are executed:

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| **SingleConfigStrategy** | Runs one config | Default behavior, single execution path |
| **ShadowStrategy** | Runs primary config in foreground, others in background | Test alternatives without blocking main flow |
| **MultiBranchStrategy** | Runs all configs in parallel, returns all results | Get user feedback on multiple variants |
| **RoundRobinStrategy** | Cycles through configs on each call | Multi-variate testing |

### 3. Experiments
The `@experiment` decorator wraps your functions to automatically inject configurations and track results.

## Quick Start

### Installation

```bash
pip install spearmint-framework
```

### Basic Example

```python
from spearmint import Spearmint, Config

# Initialize with a configuration
mint = Spearmint(configs=[{"model": "gpt-4", "temperature": 0.7}])

# Decorate your function
@mint.experiment()
def generate_text(prompt: str, config: Config) -> str:
    # config is automatically injected
    return f"Using {config['model']} at temp {config['temperature']}: {prompt}"

# Call normally - Spearmint handles the rest
result = generate_text("Hello world")
print(result)  # "Using gpt-4 at temp 0.7: Hello world"
```

### Running Experiments Explicitly

```python
from spearmint import Spearmint, Config

with Spearmint.run(generate_text) as runner:
    results = runner("Hello world")
    print(results.main_result.result)

@mint.experiment()
async def generate_text_async(prompt: str, config: Config) -> str:
    return f"Async {config['model']}: {prompt}"

async def run_async() -> None:
    async with Spearmint.arun(generate_text_async) as runner:
        results = await runner("Hello async")
        print(results.main_result.result)
```

### Comparing Multiple Configurations

```python
from spearmint import Spearmint
from spearmint.strategies import MultiBranchStrategy

mint = Spearmint(
    strategy=MultiBranchStrategy,
    configs=[
        {"model": "gpt-4o", "temperature": 0.0},
        {"model": "gpt-4o", "temperature": 0.5},
        {"model": "gpt-4o-mini", "temperature": 0.0},
    ]
)

@mint.experiment()
def generate_summary(text: str, config: dict) -> str:
    # Your implementation here
    return f"Summary using {config['model']}"

# Returns a BranchContainer with results from all configs
branches = generate_summary("Long text to summarize...")

for branch in branches:
    print(f"Config: {branch.config_id}")
    print(f"Result: {branch.output}")
    print(f"Duration: {branch.duration}s")
```

## Advanced Features

### Dynamic Value Expansion

Generate multiple configurations from any iterable:

```python
from spearmint.config import DynamicValue

def temp_generator():
    for temp in range(0, 101, 50):
        yield temp / 100.0

configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "max_tokens": DynamicValue(range(250, 501, 250)),
    "temperature": DynamicValue(temp_generator())
}]
# This creates 12 unique configurations (2 models × 2 max_tokens × 3 temperatures)

mint = Spearmint(configs=configs)
```

### Typed Configurations with Pydantic

Use type-safe configuration models:

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

# Bind your model to a path in the config
@mint.experiment(bindings={LLMConfig: ""})
def generate(prompt: str, config: LLMConfig) -> str:
    # config is now a typed LLMConfig object with IDE support
    return f"{config.model}: {prompt}"
```

### Nested Configuration Binding

Access nested configuration values:

```python
from pydantic import BaseModel

class ModelConfig(BaseModel):
    model: str
    temperature: float

configs = [{
    "llm": {
        "model_config": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
}]

mint = Spearmint(configs=configs)

# Bind to nested path using dot notation
@mint.experiment(bindings={ModelConfig: "llm.model_config"})
def generate(prompt: str, config: ModelConfig) -> str:
    return f"{config.model}: {prompt}"
```

### Shadow Testing in Production

Test new configurations without impacting your main code path:

```python
from spearmint import Spearmint
from spearmint.config import Config
from spearmint.strategies import ShadowStrategy

mint = Spearmint(
    strategy=ShadowStrategy,
    configs=[
        {"model": "gpt-4"},        # Primary (index 0)
        {"model": "gpt-5-beta"},   # Shadow
    ]
)

@mint.experiment()
def api_call(query: str, config: Config) -> str:
    # Primary result returned immediately
    # Shadow runs in background for comparison
    return make_llm_call(config['model'], query)

result = api_call("What is AI?")  # Uses gpt-4, logs gpt-5-beta in background
```

### Offline Evaluation with Datasets

Run experiments on datasets and evaluate results:

```python
from spearmint import Spearmint
from spearmint.config import Config

mint = Spearmint(configs=[{"id": 1}])

@mint.experiment()
def process_item(input_text: str, config: Config) -> str:
    return f"{config['id']}-{input_text}"

# Run on a dataset (JSONL file)
with Spearmint.run(process_item) as runner:
    results = runner("hello")
# Each line in JSONL: {"input_text": "hello", "expected": "1-hello"}
```

### Custom Evaluators

Evaluate experiment results with custom metrics:

```python
def accuracy(expected: str, trace: dict) -> float:
    # Compare expected vs actual output
    actual = trace['data']['spans'][0]['outputs']['output']
    return 1.0 if expected == actual else 0.0

mint = Spearmint(
    configs=[{"id": 1}],
)

@mint.experiment(evaluators=[accuracy])
def process(input_text: str, config: dict) -> str:
    return f"{config['id']}-{input_text}"

# Evaluators run automatically after dataset processing
with Spearmint.run(process) as runner:
    results = runner("hello")
```

## Real-World Examples

### Example 1: FastAPI Experiment with Multiple Models

```python
from fastapi import FastAPI
from spearmint import Spearmint
from spearmint.strategies import ShadowStrategy
from spearmint.config import Config, DynamicValue

app = FastAPI()

mint = Spearmint(
    strategy=ShadowStrategy,
    configs=[{
        "model": DynamicValue(["gpt-4o", "gpt-4o-mini", "gpt-5"]),
        "temperature": DynamicValue([0.0, 0.5, 1.0])
    }]
    # Creates 9 configs, first is primary, rest are shadows
)

@app.post("/summarize")
async def summarize(text: str):
    result = await _generate_summary(text)
    return {"summary": result}

@mint.experiment()
async def _generate_summary(text: str, config: Config) -> str:
    # Primary config executes and returns
    # Other 8 configs log results in background
    response = await openai_call(
        model=config['model'],
        temperature=config['temperature'],
        text=text
    )
    return response.text
```

### Example 2: Batch Processing with Multiple Strategies

```python
from spearmint import Spearmint
from spearmint.config import Config
from spearmint.strategies import MultiBranchStrategy

mint = Spearmint(configs=[
    {"algorithm": "v1", "threshold": 0.5},
    {"algorithm": "v2", "threshold": 0.7},
])

@mint.experiment(strategy=MultiBranchStrategy)
def process_document(doc_id: str, content: str, config: Config) -> dict:
    algo = config['algorithm']
    threshold = config['threshold']
    
    # Your processing logic
    result = run_algorithm(algo, content, threshold)
    
    return {
        "doc_id": doc_id,
        "algorithm": algo,
        "result": result
    }

# Process a dataset
with Spearmint.run(process_document) as runner:
    results = runner("doc-id", "document content")
```

## Tracing and Logging

Spearmint integrates with MLflow for automatic experiment tracking:

```python
import mlflow

# All functions decorated with @mint.experiment are logged to MLflow automatically
# using the traces API.

# Experiment runs and evaluations use the data from traces to calculate metrics.

# Access traces programmatically
traces = mlflow.search_traces()
for trace in traces:
    print(trace.to_dict())
```

## Configuration Files

### YAML Configuration
```yaml
# config.yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
```

```python
mint = Spearmint(configs=["config.yaml"])
```

### Directory of Configs
```python
# Loads all YAML files in the directory
mint = Spearmint(configs=["configs/"])
```

## API Reference

### Spearmint Class

```python
Spearmint(
    strategy: type[Strategy] = SingleConfigStrategy,
    configs: list[dict | Config | str | Path] = None,
    bindings: dict[type[BaseModel], str] = None,
    evaluators: Sequence[Callable] = None
)
```

### @experiment Decorator

```python
@mint.experiment(
    strategy: type[Strategy] = None,       # Override default strategy
    configs: list = None,                  # Override default configs
    bindings: dict = None,                 # Override default binding
    evaluators: Sequence[Callable] = None  # Set custom evaluators
)
```

### Branch Object

Returned by MultiBranchStrategy, contains execution details:

```python
branch.config_id    # Configuration identifier
branch.config       # Configuration used
branch.output       # Function result
branch.status       # "success", "failed", "pending", "skipped"
branch.duration     # Execution time in seconds
branch.exception_info  # Error details if failed
```

## When to Use Spearmint

**Good use cases:**
- Comparing ML model outputs (different models, parameters, prompts)
- A/B testing algorithms or business logic
- Shadow testing new code against production
- Running systematic experiments on datasets
- Parameter tuning and optimization

**Not ideal for:**
- Simple parameter passing (just use function arguments)
- One-off scripts with no variants
- Performance-critical hot paths (adds overhead)

## Roadmap
- Integrate tracing capabilities
- Add evaluation to experiment lifecycle
- Add hooks for customizing behavior
- More built-in strategies
  - Sampling-based strategies
  - Adaptive strategies based on results
- Common config types (e.g., OpenAIModelConfig, DocumentIntelligenceParseConfig)
- Azure-specific examples (Foundry Traces, Application Configuration A/B test (preview))
- Enhance typing and IDE support with generics
- Better documentation and examples

## Contributing

Contributions welcome!

## License

See LICENSE file for details.
