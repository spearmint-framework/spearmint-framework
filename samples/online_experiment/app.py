from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from spearmint import Spearmint
from spearmint.strategies import (
    RoundRobinStrategy,  # noqa: F401
)

# Initialize FastAPI app
app = FastAPI(
    title="Text Summarization API",
    description="API for generating text summaries using OpenAI",
    version="1.0.0",
)

mint: Spearmint = Spearmint(configs=["samples/online_experiment/config.yaml"])


# Request model
class SummarizeRequest(BaseModel):
    text: str
    max_length: int | None = 150
    model: str | None = "gpt-3.5-turbo"


# Response model
class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int


class ModelConfig(BaseModel):
    model: str
    prompt: str
    temperature: float = 0.3


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint"""
    return {"message": "Text Summarization API is running"}


@app.get("/summarize", response_model=SummarizeResponse)
async def summarize_text() -> SummarizeResponse:
    """
    Generate a summary of the provided text using OpenAI

    Args:
        request: SummarizeRequest containing the text to summarize

    Returns:
        SummarizeResponse with the generated summary and metadata
    """
    request = SummarizeRequest(
        text="OpenAI's mission is to ensure that artificial general intelligence benefits all of humanity. We are committed to building safe and beneficial AI systems, and to conducting research that advances the field of AI in a responsible manner.",
        max_length=150,
    )
    try:
        # model_config: ModelConfig is not passed here. It will be injected by Spearmint
        summary = _generate_summary(text=request.text, max_length=request.max_length)

        return SummarizeResponse(
            summary=summary,
            original_length=len(request.text.split()),
            summary_length=len(summary.split()),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@mint.experiment(bindings={ModelConfig: "llm.model_config"})
def _generate_summary(
    text: str,
    model_config: ModelConfig,
    max_length: int | None = 150,
) -> str:
    # Create the prompt for summarization
    prompt = model_config.prompt.format(max_length=max_length, text=text)

    # Determine max_tokens for the API call
    max_tokens = min((max_length or 150) + 50, 500)

    # Fake OpenAI API call
    response = f"fake response {model_config.model} {model_config.temperature} {model_config.prompt[:20]}..."

    print(f"""##### MAKING FAKE API CALL #####
    response = client.chat.completions.create(
        model="{model_config.model}",
        messages=[
            {{ "role": "system", "content": "{prompt}" }},
        ],
        max_tokens={max_tokens},
        temperature={model_config.temperature},
    )
    
    response[{response}]\n\n""")

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
