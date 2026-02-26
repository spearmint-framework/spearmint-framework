# Shadow Testing in Production

Safely test new configurations in production by running them in the background without affecting your main application flow.

## Problem

When deploying new features or configurations to production, you face a dilemma:

- **Risk**: Switching directly could break production
- **Uncertainty**: Staging environments don't reflect real traffic
- **Need**: You want to test with real data without affecting users

## Solution

Use **shadow testing**: run your main configuration in the foreground and test variants in the background. Users see only the main result while you collect metrics on alternatives.

## How Shadow Testing Works

``````python
from spearmint import Spearmint

mint = Spearmint(
    configs=[
        {"model": "gpt-4"},        # Primary (index 0)
        {"model": "gpt-5-beta"},   # Shadow (background)
    ]
)

@mint.experiment()
def api_call(query: str, config: Config) -> str:
    return make_llm_call(config['model'], query)

# Returns gpt-4 result immediately
# gpt-5-beta runs in background for comparison
result = api_call("What is AI?")
``````

**Key Characteristics:**

1. **Primary config runs synchronously** - returned to user immediately
2. **Variant configs run asynchronously** - in background threads/tasks
3. **Errors isolated** - variant failures don't affect primary result
4. **Metrics collected** - compare performance and outputs

## Basic Usage

### Default Shadow Behavior

By default, Spearmint runs with shadow-like behavior when multiple configs are present:

``````python
from spearmint import Spearmint, Config

mint = Spearmint(
    configs=[
        {"model": "gpt-4", "temperature": 0.5},       # Primary
        {"model": "gpt-3.5", "temperature": 0.7},     # Shadow
    ]
)

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return f"Using {config['model']} with temp {config['temperature']}"

if __name__ == "__main__":
    # Run experiment
    with Spearmint.run(generate) as runner:
        result = runner("Explain AI")
        
        # Main result returned immediately
        print(f"User sees: {result.main_result.result}")
        # Output: User sees: Using gpt-4 with temp 0.5
        
    # Note: Shadow variant runs in background
    # Use await_variants=True to wait for completion
``````

### Waiting for Shadow Results

To collect shadow results for comparison:

``````python
with Spearmint.run(generate, await_variants=True) as runner:
    result = runner("Explain AI")
    
    # Main result
    print(f"Main: {result.main_result.result}")
    
    # Shadow results (after completion)
    for variant in result.variant_results:
        print(f"Shadow: {variant.result}")
``````

## Production Use Case: API Testing

Test a new model version in production without risk:

``````python
from fastapi import FastAPI
from pydantic import BaseModel
from spearmint import Spearmint
from typing import Annotated
from spearmint.configuration import Bind
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

class ModelConfig(BaseModel):
    model: str
    temperature: float

mint = Spearmint(
    configs=[
        {"model": "gpt-4", "temperature": 0.5},         # Production
        {"model": "gpt-4-turbo", "temperature": 0.5},   # Testing
    ]
)

@mint.experiment()
def generate_summary(text: str, model_config: ModelConfig) -> str:
    """Generate summary using configured model."""
    # Call your LLM API
    response = llm_api_call(
        model=model_config.model,
        prompt=f"Summarize: {text}",
        temperature=model_config.temperature
    )
    
    # Log for comparison
    logger.info(f"Model {model_config.model}: {response}")
    
    return response

@app.post("/summarize")
async def summarize(text: str):
    """API endpoint with shadow testing."""
    # Primary model returns immediately to user
    # Shadow model runs in background for metrics
    summary = generate_summary(text)
    
    return {"summary": summary}
``````

**Result:**

- User receives `gpt-4` response immediately
- `gpt-4-turbo` runs in background
- Logs collected for comparison
- No user impact if shadow variant fails

## Async Shadow Testing

Use async experiments for non-blocking shadow execution:

``````python
from spearmint import Spearmint, Config

mint = Spearmint(
    configs=[
        {"model": "gpt-4"},
        {"model": "claude-3"},
    ]
)

@mint.experiment()
async def async_generate(prompt: str, config: Config) -> str:
    """Async experiment function."""
    response = await async_llm_call(config['model'], prompt)
    return response

# Use async context manager
async def main():
    async with Spearmint.arun(async_generate) as runner:
        result = await runner("Explain quantum computing")
        
        # Main result available immediately
        print(f"User sees: {result.main_result.result}")
        
    # Shadow runs as background async task
``````

## Comparing Results

Collect and compare shadow vs. primary results:

``````python
from spearmint import Spearmint, Config

mint = Spearmint(
    configs=[
        {"model": "gpt-4", "temperature": 0.5},
        {"model": "gpt-4", "temperature": 0.9},
        {"model": "claude-3", "temperature": 0.5},
    ]
)

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return llm_call(config['model'], prompt, config['temperature'])

# Run with shadow variants
with Spearmint.run(generate, await_variants=True) as runner:
    result = runner("What is machine learning?")
    
    # Primary (production) result
    main = result.main_result
    print(f"Primary: {main.config_id}")
    print(f"Result: {main.result}")
    
    # Shadow variants
    for variant in result.variant_results:
        print(f"\nShadow: {variant.config_id}")
        print(f"Result: {variant.result}")
        
        # Compare metrics
        print(f"Execution time: {variant.execution_time_ms}ms")
        
        # Compare outputs
        if variant.result == main.result:
            print("✓ Same output")
        else:
            print("✗ Different output")
``````

## Error Handling

Shadow failures don't affect primary results:

``````python
@mint.experiment()
def robust_api_call(query: str, config: Config) -> str:
    try:
        return make_llm_call(config['model'], query)
    except Exception as e:
        logger.error(f"Error with {config['model']}: {e}")
        raise  # Shadow will log error but not affect primary

# Primary succeeds even if shadow fails
result = robust_api_call("Test query")
``````

## Best Practices

### 1. Start with One Shadow

Begin with primary + one shadow variant:

``````python
configs = [
    {"model": "production-model"},  # Primary
    {"model": "new-model"},         # Shadow
]
``````

### 2. Monitor Shadow Performance

Track shadow execution metrics:

``````python
with Spearmint.run(generate, await_variants=True) as runner:
    result = runner(prompt)
    
    for variant in result.variant_results:
        # Log metrics
        logger.info(
            f"Shadow {variant.config_id}: "
            f"{variant.execution_time_ms}ms"
        )
``````

### 3. Gradual Rollout

Once shadow testing succeeds, swap configurations:

``````python
# Phase 1: Shadow testing
configs = [
    {"model": "gpt-4"},         # Primary
    {"model": "gpt-4-turbo"},   # Shadow
]

# Phase 2: After validation, promote shadow to primary
configs = [
    {"model": "gpt-4-turbo"},   # Primary (promoted!)
    {"model": "gpt-4"},         # Shadow (keep for comparison)
]
``````

### 4. Use Structured Logging

Log shadow results for analysis:

``````python
import structlog

logger = structlog.get_logger()

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    result = llm_call(config['model'], prompt)
    
    # Structured logging for analysis
    logger.info(
        "experiment_result",
        config_id=config.id,
        model=config['model'],
        prompt_length=len(prompt),
        result_length=len(result),
    )
    
    return result
``````

## Complete Example: FastAPI Shadow Testing

``````python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Annotated
from spearmint import Spearmint
from spearmint.configuration import Bind
import logging
import time

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

class ModelConfig(BaseModel):
    model: str
    prompt: str
    temperature: float = 0.3

class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 150

class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int

mint = Spearmint(
    configs=[
        "config/main.yaml",      # Primary
        "config/shadow.yaml",    # Shadow
    ]
)

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """Generate summary with shadow testing."""
    try:
        summary = _generate_summary(
            text=request.text,
            max_length=request.max_length
        )
        
        return SummarizeResponse(
            summary=summary,
            original_length=len(request.text.split()),
            summary_length=len(summary.split()),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )

@mint.experiment()
def _generate_summary(
    text: str,
    model_config: Annotated[ModelConfig, Bind("llm.model_config")],
    max_length: int = 150,
) -> str:
    """Generate summary using configured model.
    
    Primary config runs synchronously, shadow runs in background.
    """
    prompt = model_config.prompt.format(
        max_length=max_length,
        text=text
    )
    
    # Call LLM API
    response = llm_api_call(
        model=model_config.model,
        prompt=prompt,
        temperature=model_config.temperature,
        max_tokens=min(max_length + 50, 500)
    )
    
    # Log for shadow comparison
    logger.info(
        f"Model {model_config.model}: "
        f"Generated {len(response)} chars"
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
``````

## See Also

- [Compare Configurations](compare-configurations.md) - Analyze shadow results
- [Integrate FastAPI](integrate-fastapi.md) - FastAPI integration patterns
- [Experiment Lifecycle](../explanation/experiment-lifecycle.md) - How experiments execute
- [Cookbook: Shadow Traffic Example](https://github.com/spearmint-framework/spearmint-framework/blob/main/cookbook/online_experiments/shadow_traffic_app/)
