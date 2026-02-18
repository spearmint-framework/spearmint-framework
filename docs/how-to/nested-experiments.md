# Nested Experiments

Run experiments within experiments to test configurations at multiple levels of your application.

## Problem

Complex applications have multiple components, each with their own configuration options:

- **LLM settings**: Model, temperature, max tokens
- **Retrieval settings**: Top-k, similarity threshold
- **Processing settings**: Batch size, timeout

Testing all combinations manually across layers is impractical.

## Solution

Use **nested experiments**: experiments that call other experiments. Each level can have its own configurations, and Spearmint automatically handles the cartesian product across all levels.

## Basic Usage

Define experiments at multiple levels:

``````python
from spearmint import Spearmint, Config

mint = Spearmint()

# Inner experiment: retrieval configuration
@mint.experiment(configs=[
    {"top_k": 3},
    {"top_k": 5},
])
def retrieve(query: str, config: Config) -> list[str]:
    """Retrieve documents with configured top_k."""
    return search_database(query, top_k=config["top_k"])

# Outer experiment: LLM configuration
@mint.experiment(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5"},
])
def generate_response(query: str, config: Config) -> str:
    """Generate response using retrieved documents."""
    # Call inner experiment
    documents = retrieve(query)
    
    # Use outer config
    return llm_call(config["model"], documents)

if __name__ == "__main__":
    with Spearmint.run(generate_response, await_variants=True) as runner:
        result = runner("What is AI?")
        
        # Main result uses first config from each level
        print(f"Main: {result.main_result.result}")
        
        # Variants test all combinations: 2 outer × 2 inner = 4 total
        for variant in result.variant_results:
            print(f"Variant: {variant.result}")
``````

## How Nested Experiments Work

### Configuration Cartesian Product

Nested experiments create combinations across all levels:

``````python
# Outer: 2 configs
@mint.experiment(configs=[
    {"model": "gpt-4"},      # Outer config 0
    {"model": "gpt-3.5"},    # Outer config 1
])
def outer(config: Config) -> str:
    return inner()

# Inner: 2 configs
@mint.experiment(configs=[
    {"temperature": 0.5},    # Inner config 0
    {"temperature": 0.9},    # Inner config 1
])
def inner(config: Config) -> str:
    return f"temp={config['temperature']}"

# Total combinations: 2 × 2 = 4
# (gpt-4, 0.5), (gpt-4, 0.9), (gpt-3.5, 0.5), (gpt-3.5, 0.9)
``````

### Execution Context

Spearmint maintains execution context across nested calls:

1. **Main case**: First config from each experiment
2. **Variant cases**: All other combinations
3. **Context propagation**: Each variant maintains consistent configs across all nested experiments

## Complete Example

Here's a practical example with multiple nesting levels:

``````python
from spearmint import Config, Spearmint

mint = Spearmint()

# Level 3: Data processing
@mint.experiment(configs=[
    {"batch_size": 10},
    {"batch_size": 5},
])
def process_data(data: list, config: Config) -> list:
    """Process data in batches."""
    batch_size = config["batch_size"]
    return [data[i:i+batch_size] for i in range(0, len(data), batch_size)]

# Level 2: Retrieval
@mint.experiment(configs=[
    {"top_k": 3},
    {"top_k": 5},
])
def retrieve(query: str, config: Config) -> list[str]:
    """Retrieve and process documents."""
    # Simulate retrieval
    docs = [f"doc_{i}" for i in range(10)]
    
    # Nested call to process_data
    processed = process_data(docs[:config["top_k"]])
    
    return processed

# Level 1: Generation
@mint.experiment(configs=[
    {"model": "gpt-4", "temperature": 0.5},
    {"model": "gpt-3.5", "temperature": 0.9},
])
def generate(query: str, config: Config) -> str:
    """Generate response using retrieval."""
    # Nested call to retrieve
    docs = retrieve(query)
    
    return f"Model {config['model']}: {len(docs)} doc groups"

if __name__ == "__main__":
    with Spearmint.run(generate, await_variants=True) as runner:
        result = runner("What is AI?")
        
        print(f"Main: {result.main_result.result}")
        
        # All combinations: 2 × 2 × 2 = 8 total cases
        print(f"\nTotal variants: {len(result.variant_results)}")
        for i, variant in enumerate(result.variant_results):
            print(f"Variant {i+1}: {variant.result}")
``````

## Accessing Nested Configuration

Get configuration details for any level:

``````python
@mint.experiment(configs=[{"multiplier": 10}, {"multiplier": 0}])
def inner(num: int, config: Config) -> int:
    return num * config["multiplier"]

@mint.experiment(configs=[{"addition": 10}, {"addition": 0}])
def outer(value: int, config: Config) -> str:
    inner_result = inner(value)
    return f"Result: {config['addition'] + inner_result}"

if __name__ == "__main__":
    with Spearmint.run(outer, await_variants=True) as runner:
        result = runner(2)
        
    # Access configs for each experiment level
    main_case = result.main_result.experiment_case
    
    outer_config_id = main_case.get_config_id(outer.__qualname__)
    inner_config_id = main_case.get_config_id(inner.__qualname__)
    
    outer_config = main_case._configs[outer_config_id]
    inner_config = main_case._configs[inner_config_id]
    
    print(f"Outer: addition={outer_config['addition']}")
    print(f"Inner: multiplier={inner_config['multiplier']}")
``````

## Use Cases

### 1. RAG Pipeline Testing

Test combinations of retrieval and generation settings:

``````python
@mint.experiment(configs=[
    {"embedding_model": "ada-002"},
    {"embedding_model": "ada-003"},
])
def embed_and_retrieve(query: str, config: Config) -> list[str]:
    embeddings = embed(query, config["embedding_model"])
    return vector_search(embeddings, top_k=5)

@mint.experiment(configs=[
    {"model": "gpt-4", "temperature": 0.7},
    {"model": "gpt-3.5", "temperature": 0.5},
])
def answer_question(query: str, config: Config) -> str:
    context = embed_and_retrieve(query)
    return generate_answer(context, config)
``````

### 2. Multi-Stage Data Processing

Test configurations across processing stages:

``````python
@mint.experiment(configs=[
    {"normalize": True},
    {"normalize": False},
])
def preprocess(data: list, config: Config) -> list:
    if config["normalize"]:
        return [normalize(x) for x in data]
    return data

@mint.experiment(configs=[
    {"algorithm": "kmeans"},
    {"algorithm": "dbscan"},
])
def cluster(data: list, config: Config) -> dict:
    processed = preprocess(data)
    return run_clustering(processed, config["algorithm"])
``````

### 3. Cascading Model Calls

Test different model combinations:

``````python
@mint.experiment(configs=[
    {"classifier": "distilbert"},
    {"classifier": "roberta"},
])
def classify_intent(text: str, config: Config) -> str:
    return classify(text, config["classifier"])

@mint.experiment(configs=[
    {"responder": "gpt-4"},
    {"responder": "claude-3"},
])
def generate_response(text: str, config: Config) -> str:
    intent = classify_intent(text)
    return generate(intent, config["responder"])
``````

## Best Practices

### 1. Start with Two Levels

Begin with simple nesting before adding complexity:

``````python
# Start simple: 2 levels
@mint.experiment(configs=[...])
def inner(config: Config):
    pass

@mint.experiment(configs=[...])
def outer(config: Config):
    return inner()
``````

### 2. Limit Configuration Count

Be mindful of exponential growth:

``````python
# 3 configs × 4 configs × 2 configs = 24 total combinations!
@mint.experiment(configs=[...])  # 3 configs
def level1(config: Config):
    return level2()

@mint.experiment(configs=[...])  # 4 configs
def level2(config: Config):
    return level3()

@mint.experiment(configs=[...])  # 2 configs
def level3(config: Config):
    pass
``````

### 3. Use Meaningful Names

Name experiments clearly to track nested configs:

``````python
@mint.experiment(configs=[...])
def retrieval_stage(query: str, config: Config):
    """First stage: document retrieval."""
    pass

@mint.experiment(configs=[...])
def generation_stage(query: str, config: Config):
    """Second stage: response generation."""
    docs = retrieval_stage(query)
    pass
``````

### 4. Log Nested Context

Track which configs are used at each level:

``````python
import logging

logger = logging.getLogger(__name__)

@mint.experiment(configs=[...])
def inner(config: Config):
    logger.info(f"Inner config: {config}")
    pass

@mint.experiment(configs=[...])
def outer(config: Config):
    logger.info(f"Outer config: {config}")
    return inner()
``````

## Context Isolation

Each experiment case maintains isolated context:

``````python
@mint.experiment(configs=[
    {"value": 1},
    {"value": 2},
])
def inner(config: Config) -> int:
    return config["value"]

@mint.experiment(configs=[
    {"multiplier": 10},
    {"multiplier": 100},
])
def outer(config: Config) -> int:
    # Inner always uses the same config index as outer
    # in the same experiment case
    result = inner()
    return result * config["multiplier"]

# Main case: (value=1, multiplier=10) → 1 × 10 = 10
# Variant 1: (value=1, multiplier=100) → 1 × 100 = 100
# Variant 2: (value=2, multiplier=10) → 2 × 10 = 20
# Variant 3: (value=2, multiplier=100) → 2 × 100 = 200
``````

## Advanced: Dynamic Nesting

Conditionally call nested experiments:

``````python
@mint.experiment(configs=[
    {"use_cache": True},
    {"use_cache": False},
])
def retrieve_with_cache(query: str, config: Config) -> list:
    if config["use_cache"]:
        return get_from_cache(query)
    else:
        return expensive_retrieval(query)

@mint.experiment(configs=[
    {"model": "gpt-4"},
    {"model": "gpt-3.5"},
])
def generate(query: str, config: Config) -> str:
    # Conditionally use nested experiment
    if config["model"] == "gpt-4":
        docs = retrieve_with_cache(query)
    else:
        docs = simple_retrieval(query)
    
    return generate_response(docs, config)
``````

## See Also

- [Experiment Lifecycle](../explanation/experiment-lifecycle.md) - How nested execution works
- [Context Isolation](../explanation/context-isolation.md) - Understanding experiment context
- [Compare Configurations](compare-configurations.md) - Analyze nested results
- [Cookbook: Nested Experiment Example](https://github.com/spearmint-framework/spearmint-framework/blob/main/cookbook/advanced/nested_experiment.py)
