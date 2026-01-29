# Spearmint Cookbook

Small, focused recipes for common Spearmint workflows. Run any sample with:

```bash
uv run python cookbook/<sample>.py
```

## Recipes

### Basic Examples
- `simple_experiment.py` - Minimal experiment with a single config.
- `basic_pipeline.py` - Insert a configured step into a small pipeline.
- `async_experiment.py` - Async experiment with variant results.

### Configuration Management
- `dynamic_config.py` - DynamicValue grid generation.
- `typed_config.py` - Bind config data to a typed model.
- `yaml_configs.py` - Load configs from YAML files and paths.

### Advanced Workflows
- `dataset_processing.py` - Iterate over a JSONL dataset.
- `nested_experiment.py` - Nested experiments with multiple configs.

### Online Experiments
- `online_experiments/basic_app/` - Basic FastAPI app with config injection.
- `online_experiments/ab_test_app/` - Sticky A/B test FastAPI app.
- `online_experiments/shadow_traffic_app/` - Shadow-traffic FastAPI app.
