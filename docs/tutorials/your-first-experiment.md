# Your First Experiment

Build a practical LLM experiment from scratch.

**Time estimate:** 15 minutes

---

## What You'll Build

A text summarization experiment that compares:
- Different LLM models (GPT-4 vs GPT-3.5-turbo)
- Different temperature values (0.0, 0.5, 1.0)
- Different max_tokens settings

---

## Prerequisites

- Completed [Getting Started](getting-started.md)
- OpenAI API key (or similar LLM API)
- Basic Python knowledge

---

## Step 1: Setup

Install dependencies:

``````bash
pip install spearmint-framework openai
``````

Set your API key:

``````bash
export OPENAI_API_KEY="your-key-here"
``````

---

## Step 2: Define Configurations

Create a file `summarize_experiment.py`:

``````python
from spearmint import Spearmint, Config
from spearmint.config import DynamicValue
import openai

# Define parameter sweep
configs = [{
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0]),
    "max_tokens": 150
}]
# Creates 6 configurations (2 models × 3 temperatures)

mint = Spearmint(configs=configs)
``````

---

## Step 3: Create Experiment Function

``````python
@mint.experiment()
def summarize_text(text: str, config: Config) -> str:
    """Summarize text using configured LLM parameters."""
    response = openai.chat.completions.create(
        model=config['model'],
        temperature=config['temperature'],
        max_tokens=config['max_tokens'],
        messages=[
            {"role": "system", "content": "Summarize the following text concisely."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content
``````

---

## Step 4: Run Single Config

Test with one configuration (first config by default):

``````python
if __name__ == "__main__":
    sample_text = """
    Artificial intelligence has transformed many industries. Machine learning
    algorithms can now process vast amounts of data, identifying patterns that
    humans might miss. Deep learning, a subset of machine learning, has been
    particularly successful in areas like computer vision and natural language
    processing.
    """
    
    result = summarize_text(sample_text)
    print(f"Summary: {result}")
``````

Run it:

``````bash
python summarize_experiment.py
``````

---

## Step 5: Compare Multiple Configs

Use `MultiBranchStrategy` to test all configurations:

``````python
from spearmint.strategies import MultiBranchStrategy

mint = Spearmint(
    strategy=MultiBranchStrategy,
    configs=configs
)

@mint.experiment()
def summarize_text(text: str, config: Config) -> str:
    # ... same as before
    pass

if __name__ == "__main__":
    sample_text = "..."  # Same as before
    
    with Spearmint.run(summarize_text, await_variants=True) as runner:
        results = runner(sample_text)
        
        # Print all results
        print(f"Main ({results.main_result.config}):")
        print(f"  {results.main_result.result}\n")
        
        for i, variant in enumerate(results.variant_results, 1):
            print(f"Variant {i} ({variant.config}):")
            print(f"  {variant.result}\n")
``````

---

## Step 6: Add Type Safety

Use Pydantic for type-safe configs:

``````python
from pydantic import BaseModel, Field
from typing import Annotated
from spearmint.config import Bind

class LLMConfig(BaseModel):
    model: str = Field(pattern="^gpt-")
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(gt=0)

@mint.experiment()
def summarize_text(
    text: str,
    config: Annotated[LLMConfig, Bind("")]
) -> str:
    """Now config is typed with IDE support."""
    response = openai.chat.completions.create(
        model=config.model,  # Type-safe access
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        messages=[...]
    )
    return response.choices[0].message.content
``````

---

## Next Steps

**Try these enhancements:**

1. **Add evaluation metrics:**
   ``````python
   def quality_score(expected: str, trace: dict) -> float:
       # Implement scoring logic
       pass
   
   @mint.experiment(evaluators=[quality_score])
   def summarize_text(...):
       pass
   ``````

2. **Test on a dataset:**
   Create `dataset.jsonl` with test cases and run batch evaluation.

3. **Use shadow testing:**
   Test new models in production without affecting users.

**Learn more:**
- [Multi-Config Experiments](multi-config-experiments.md)
- [Testing Experiments](../how-to/testing-experiments.md)
- [Configuration System](../reference/configuration.md)
