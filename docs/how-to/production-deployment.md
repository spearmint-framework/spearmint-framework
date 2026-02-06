# Production Deployment

Best practices for deploying Spearmint experiments to production.

## Shadow Testing

Test new configurations without impacting users:

``````python
from spearmint.strategies import ShadowStrategy

mint = Spearmint(
    strategy=ShadowStrategy,
    configs=[
        {"model": "gpt-4", "env": "production"},  # Main
        {"model": "gpt-5", "env": "staging"}       # Shadow
    ]
)
``````

## Monitoring

### MLflow Integration

Track all experiments:
``````python
import mlflow

# Automatic tracing
@mint.experiment()
def api_call(request: str, config: Config) -> str:
    return process(request, config)

# Query traces
traces = mlflow.search_traces(filter_string="status = 'OK'")
``````

### Custom Metrics

``````python
from prometheus_client import Counter, Histogram

requests = Counter('spearmint_requests', 'Experiment requests')
latency = Histogram('spearmint_latency', 'Execution time')

@mint.experiment()
def monitored_call(data: str, config: Config) -> str:
    requests.inc()
    with latency.time():
        return process(data, config)
``````

## Configuration Management

### Environment-Based Configs

``````python
import os

env = os.getenv("ENV", "development")
config_file = f"configs/{env}.yaml"

mint = Spearmint(configs=[config_file])
``````

## See Also

- [Testing](testing-experiments.md)
- [Debugging](debugging.md)
