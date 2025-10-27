# spearmint-framework

An opinionated framework for running rapid llm-based experiments.

## Installation

Base installation:

```bash
pip install spearmint-framework
```

With MLflow logging support:

```bash
pip install 'spearmint-framework[mlflow]'
```

## Quick Start

```python
from spearmint import Spearmint
from spearmint.strategies import RoundRobinStrategy

mint = Spearmint()
mint.configs = [
	{"delta": 1},
	{"delta": 5},
]

@mint.experiment(RoundRobinStrategy())
async def add(x: int, config: dict) -> int:
	return x + config["delta"]

# In an async context:
result1 = await add(10)  # 11
result2 = await add(10)  # 15
```

## MLflow Logging

Spearmint provides an optional MLflow backend (`MLflowLogger`) for structured
experiment tracking. Install the `mlflow` extra first (see above).

```python
from spearmint.logging import MLflowLogger
from spearmint.branch import Branch

logger = MLflowLogger(tracking_uri="file:./mlruns", experiment_name="demo")
run_id = "exp_run_1"
logger.start_run(run_id)
logger.log_params(run_id, {"model": "gpt", "lr": 0.01})
logger.log_metrics(run_id, {"accuracy": 0.92})

# Log a branch execution artifact
branch = Branch.start("cfg1", {"delta": 1})
branch.mark_success(output=42)
logger.log_branch(run_id, branch)
logger.end_run(run_id)
```

This creates MLflow params, metrics, and a JSON artifact per branch with full
execution details (`status`, `duration`, `output`, and any exception info).

## Development

Run tests:

```bash
uv run pytest -q
```

## License

MIT
