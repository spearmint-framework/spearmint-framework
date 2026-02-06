# Debugging Configuration Issues

Guide to troubleshooting common Spearmint configuration problems.

## Common Issues

### Config Not Injected

**Problem:** Function doesn't receive config parameter

**Solution:** Ensure function signature includes `config` parameter:
``````python
@mint.experiment()
def my_func(input: str, config: Config) -> str:  # ✅ Has config
    return f"{config['model']}: {input}"
``````

### Key Errors

**Problem:** `KeyError` when accessing config

**Solution:** Use `.get()` with defaults or validate config:
``````python
# Option 1: Use defaults
model = config.get('model', 'gpt-3.5-turbo')

# Option 2: Validate with Pydantic
class ValidConfig(BaseModel):
    model: str
``````

### Type Binding Errors

**Problem:** Pydantic validation fails

**Solution:** Check config matches model schema:
``````python
class ModelConfig(BaseModel):
    temperature: float = Field(ge=0.0, le=2.0)

config = {"temperature": 3.0}  # ❌ Exceeds le=2.0
``````

## Debugging Tools

### Print Config

``````python
@mint.experiment()
def debug_config(input: str, config: Config) -> str:
    print(f"Config: {config}")
    print(f"Config ID: {config.get('__config_id__')}")
    return process(input, config)
``````

### MLflow Traces

Query execution traces:
``````python
import mlflow
traces = mlflow.search_traces()
for trace in traces:
    print(trace.to_dict())
``````

## See Also

- [Testing Experiments](testing-experiments.md)
- [Configuration Reference](../reference/configuration.md)
