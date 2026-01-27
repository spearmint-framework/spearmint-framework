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

# Bind the Pydantic model to the config parameter using Bind + Annotated
@mint.experiment()
def generate(prompt: str, config: Annotated[Config, Bind("")]) -> str:
    model_config = ModelConfig.model_validate(config.root)
    return f"Model: {model_config.model_name}, Temp: {model_config.temperature}"

if __name__ == "__main__":
    with Spearmint.run(generate) as runner:
        result = runner("Test prompt")
        print(result.main_result.result)
