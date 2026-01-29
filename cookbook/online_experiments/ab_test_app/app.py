import logging
import time

from fastapi import FastAPI, HTTPException, Request
from typing import Annotated
from pydantic import BaseModel

from spearmint import Spearmint, Config
from spearmint.configuration import Bind
from spearmint.context import RuntimeContext, runtime_context

# Initialize FastAPI app
app = FastAPI(
    title="Text Summarization API",
    description="API for generating text summaries using OpenAI",
    version="1.0.0",
)

# Use Uvicorn's configured logger so logs show up in the server console.
logger = logging.getLogger("uvicorn.error")

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    user_id = request.headers.get("x-user-id")
    user_id = user_id or request.query_params.get("user_id")
    with runtime_context() as ctx:
        ctx.set("user_id", user_id)
        response = await call_next(request)
    return response

def sticky_ab_test_config_handler(configs: list[Config], ctx: RuntimeContext) -> tuple[Config, list[Config]]:
    # hash the user_id to select a config deterministically
    user_id = ctx.get("user_id") or "default_user"
    hashed_id = hash(user_id)
    index = hashed_id % len(configs)
    logger.info("User ID: %s, Hashed ID: %d, Selected Config Index: %d", user_id, hashed_id, index)

    # Return the selected config only and no background variants
    return configs[index], []

mint: Spearmint = Spearmint(
    branch_strategy=sticky_ab_test_config_handler,
    configs=[
        "cookbook/online_experiments/ab_test_app/main_config.yaml",
        "cookbook/online_experiments/ab_test_app/variant_config.yaml",
    ]
)


class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 150


class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int


class ModelConfig(BaseModel):
    model: str
    prompt: str
    temperature: float = 0.3


@app.get("/", response_model=SummarizeResponse)
async def summarize_text() -> SummarizeResponse:
    """
    Generate a summary of the provided text using OpenAI
    """
    request = SummarizeRequest(
        text="Example text to be summarized by the API. This would be replaced by user input in a real scenario.",
        max_length=150,
    )
    try:
        # model_config: ModelConfig is not passed here. It will be injected by Spearmint
        summary = _generate_summary(text=request.text, max_length=request.max_length)
        logger.info("Summary generated: %s", summary)

        return SummarizeResponse(
            summary=summary,
            original_length=len(request.text.split()),
            summary_length=len(summary.split()),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e

# Dependency inject ModelConfig by binding the values from llm.model_config in the YAML config
# The main branch will run normally, while the variant branches run in the background
@mint.experiment()
def _generate_summary(
    text: str,
    model_config: Annotated[ModelConfig, Bind("llm.model_config")],
    max_length: int = 150,
) -> str:
    # Create the prompt for summarization
    prompt = model_config.prompt.format(max_length=max_length, text=text)

    # Determine max_tokens for the API call
    max_tokens = min((max_length or 150) + 50, 500)


    ##### Fake the API call and response #####
    # response = client.chat.completions.create(
    #     model=model_config.model,
    #     messages=[
    #         {{ "role": "system", "content": prompt }},
    #     ],
    #     max_tokens=max_tokens,
    #     temperature=model_config.temperature,
    # )

    sleep_time = 0.5
    logger.info("Simulating %s API call with %.2f seconds delay", model_config.model, sleep_time)
    time.sleep(sleep_time)

    response = f"[fake response] {model_config.model} (temp={model_config.temperature}) {prompt[:20]}..."
    
    logger.info("_generate_summary output: %s", response)

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
