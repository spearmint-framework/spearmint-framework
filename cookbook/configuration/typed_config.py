from typing import Annotated

from pydantic import BaseModel

from spearmint import Config, Spearmint
from spearmint.configuration import Bind

# Define a Pydantic model for type-safe configuration
class ModelConfig(BaseModel):
    model_name: str
    temperature: float
    max_tokens: int = 100

# Initialize Spearmint with a list of configs that match the structure
mint = Spearmint(
    configs=[
        {"model_name": "gpt-4", "temperature": 0.5},
        {"model_name": "gpt-3.5", "temperature": 0.9, "max_tokens": 50},
    ]
)

# Dependency inject ModelConfig using the configs defined above
@mint.experiment()
def generate(prompt: str, model_config: ModelConfig) -> str:
    return f"Prompt: {prompt}, Model: {model_config.model_name}, Temp: {model_config.temperature}, MaxTokens: {model_config.max_tokens}"

if __name__ == "__main__":
    with Spearmint.run(generate, await_variants=True) as runner:
        result = runner("Test prompt")
        print(result.main_result.result)
        assert result.main_result.result == "Prompt: Test prompt, Model: gpt-4, Temp: 0.5, MaxTokens: 100"
        variant_results = [variant.result for variant in result.variant_results]
        assert "Prompt: Test prompt, Model: gpt-3.5, Temp: 0.9, MaxTokens: 50" in variant_results