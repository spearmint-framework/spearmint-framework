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
| **DefaultBranchStrategy** | Runs one config | Default behavior, single execution path |
| **ShadowBranchStrategy** | Runs primary config in foreground, others in background | Test alternatives without blocking main flow |
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
from spearmint import Config, Spearmint

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

### Comparing Multiple Configurations

```python
from spearmint import Spearmint
from spearmint.strategies import MultiBranchStrategy

mint = Spearmint(
    branch_strategy=MultiBranchStrategy,
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
from spearmint.core.config import DynamicValue

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
from spearmint import Config, Spearmint
from spearmint.strategies import ShadowBranchStrategy

mint = Spearmint(
    branch_strategy=ShadowBranchStrategy,
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

## Real-World Examples

### Example 1: FastAPI Experiment with Multiple Models

```python
from fastapi import FastAPI
from spearmint import Spearmint
from spearmint.strategies import ShadowStrategy
from spearmint import Config
from spearmint.core.config import DynamicValue

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
from spearmint import Config
from spearmint.strategies import MultiBranchStrategy

mint = Spearmint(configs=[
    {"algorithm": "v1", "threshold": 0.5},
    {"algorithm": "v2", "threshold": 0.7},
])

@mint.experiment(branch_strategy=MultiBranchStrategy)
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

```

## Tracing and Telemetry

Every experiment branch executes inside a `Trace`. A trace records metadata (`trace.attributes`), links to its parent, and captures outputs/exceptions. The trace tree is exposed via `spearmint.core.trace.trace_manager`, so you can plug in custom exporters or inspect the current trace from anywhere in your code.

### Registering a custom exporter

```python
from spearmint.core.trace import TraceExporter, trace_manager

class StdoutExporter(TraceExporter):
    def on_start(self, trace):
        print(f"➡️  starting {trace.name} ({trace.trace_id})")

    def on_end(self, trace, error):
        status = "error" if error else "ok"
        print(f"⬅️  finished {trace.name}: {status}")

trace_manager.register_exporter(StdoutExporter())
```

### OpenTelemetry support

If you already collect traces with OpenTelemetry, install `opentelemetry-api` and enable the built-in exporter:

```bash
pip install opentelemetry-api
```

```python
from spearmint.core.trace import OpenTelemetryTraceExporter, trace_manager

trace_manager.register_exporter(OpenTelemetryTraceExporter())
```

Each Spearmint trace becomes a span (with args/output stored as attributes), so you can view experiment runs alongside the rest of your service telemetry.

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
    branch_strategy: type[BranchStrategy] | None = None,
    configs: list[dict | Config | str | Path] | None = None,
    bindings: dict[type[BaseModel], str] | None = None,
    evaluators: Sequence[Callable] | None = None,
)
```

### @experiment Decorator

```python
@mint.experiment(
    branch_strategy: type[BranchStrategy] | None = None,  # Override default strategy
    configs: list | None = None,                          # Override default configs
    bindings: dict | None = None,                        # Override default binding
    evaluators: Sequence[Callable] | None = None,        # Set custom evaluators
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
