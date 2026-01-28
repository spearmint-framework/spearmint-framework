# Spearmint Cookbook

The `samples/` directory is legacy/temporary and will be removed once online experiments migrate.

Small, focused recipes for common Spearmint workflows. Run any sample with:

```bash
uv run python cookbook/<sample>.py
```

## Recipes

- `simple_experiment.py` - Minimal experiment with a single config.
- `basic_pipeline.py` - Insert a configured step into a small pipeline.
- `async_step.py` - Async experiment function with `Spearmint.arun`.
- `async_experiment.py` - Async experiment with variant results.
- `dynamic_config.py` - DynamicValue grid generation.
- `dynamic_variants.py` - Run all generated variants (await background cases).
- `typed_config.py` - Bind config data to a typed model.
- `config_binding.py` - Use `Bind` for nested config paths.
- `yaml_configs.py` - Load configs from YAML files and paths.
- `dataset_processing.py` - Iterate over a JSONL dataset.
- `nested_experiment.py` - Nested experiments with multiple configs.
