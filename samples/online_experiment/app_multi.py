from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from spearmint import Spearmint
from spearmint.config import Config, DynamicValue
from spearmint.strategies import MultiBranchStrategy, SingleConfigStrategy

# Initialize FastAPI app
app = FastAPI(
    title="Text Summarization API",
    description="API for generating text summaries using OpenAI",
    version="1.0.0",
)

mint: Spearmint = Spearmint(
    # This will run all configurations in the background
    strategy=MultiBranchStrategy,
    # This will expand to create 9 unique combinations of model and temperature configs
    configs=[
        {
            "llm": {
                "model_config": {
                    "model": DynamicValue(["gpt-4o", "gpt-4o-mini", "gpt-5"]),
                    "prompt": "Summarize the following text in no more than {max_length} words:\n\n{text}",
                    "temperature": DynamicValue([0.0, 0.25, 0.5]),
                },
                "eval_summary": {
                    "summary_mod": 10,
                },
            }
        }
    ],
)


# Request model
class SummarizeRequest(BaseModel):
    text: str
    max_length: int | None = 150
    model: str | None = "gpt-3.5-turbo"


# Response model
class SummarizeResponse(BaseModel):
    summary: str
    original_word_length: int
    summary_word_length: int


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
        text="Microsoft's mission is to empower every person and every organization on the planet to achieve more.",
        max_length=150,
    )
    try:
        # model_config: ModelConfig is not passed here. It will be injected by Spearmint
        branch_container = _generate_summary(text=request.text, max_length=request.max_length)
        summaries = []
        for branch in branch_container.branches:
            summary = branch.output
            summaries.append(summary)

        eval_summaries = _evaluate_summaries(summaries)
        best_summary = eval_summaries[0]

        return SummarizeResponse(
            summary=best_summary,
            original_word_length=len(request.text.split()),
            summary_word_length=len(best_summary.split()),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@app.get("/summaries", response_model=list[SummarizeResponse])
async def summarize_all_text() -> list[SummarizeResponse]:
    """
    Generate a summary of the provided text using OpenAI

    Args:
        request: SummarizeRequest containing the text to summarize

    Returns:
        SummarizeResponse with the generated summary and metadata
    """
    request = SummarizeRequest(
        text="Microsoft's mission is to empower every person and every organization on the planet to achieve more.",
        max_length=150,
    )
    try:
        # model_config: ModelConfig is not passed here. It will be injected by Spearmint
        branch_container = _generate_summary(text=request.text, max_length=request.max_length)
        summaries = []
        for branch in branch_container.branches:
            summary = branch.output
            summaries.append(
                SummarizeResponse(
                    summary=summary,
                    original_word_length=len(request.text.split()),
                    summary_word_length=len(summary.split()),
                )
            )

        return summaries

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


@mint.experiment(strategy=SingleConfigStrategy, bindings={Config: "llm.eval_summary"})
def _evaluate_summaries(summaries: list[str], config: Config) -> list[str]:
    # Fake evaluation logic
    mod = config["summary_mod"]
    print(f"$$$$ EVALUATING SUMMARIES WITH MOD {mod} $$$$")
    evaluated_summaries: list[dict[str, str | int]] = []
    for summary in summaries:
        scored_summary = {"summary": summary, "score": len(summary) % mod}
        evaluated_summaries.append(scored_summary)

    sorted_summaries = sorted(evaluated_summaries, key=lambda x: x.get("score", 0), reverse=True)
    for s in sorted_summaries:
        print(f"Evaluated summary: {s['summary']} with score: {s['score']}")
    return [str(s["summary"]) for s in sorted_summaries]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
