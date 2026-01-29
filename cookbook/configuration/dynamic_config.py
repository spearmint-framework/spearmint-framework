from spearmint import Spearmint, Config
from spearmint.configuration import DynamicValue

# DynamicValue allows you to generate multiple configurations combinatorially
# using any iterable of values. E.G., lists, ranges, generators, etc.
# This is useful for grid search or parameter sweeping.

configs = [
    {
        # This will expand into 2 values
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        # This will expand into 3 values (1, 5, 9)
        "temperature": DynamicValue(range(1, 10, 4)),
        "static_param": "always_same",
    }
]

mint = Spearmint(configs=configs)

@mint.experiment()
def train_model(config: Config) -> str:
    return f"Model={config['model']}, Temp={config['temperature']/10.0}"

if __name__ == "__main__":
    print(f"Generated {len(mint.configs)} configurations.")

    with Spearmint.run(train_model, await_variants=True) as runner:
        result = runner()
        print(f"Run result (first config): {result.main_result.result}")

    # Verify all configurations were generated and run
    variant_results_set = {variant.result for variant in result.variant_results}
    assert result.main_result.result == "Model=gpt-4, Temp=0.1"
    assert "Model=gpt-4, Temp=0.1" not in variant_results_set
    assert "Model=gpt-4, Temp=0.5" in variant_results_set
    assert "Model=gpt-4, Temp=0.9" in variant_results_set
    assert "Model=gpt-3.5, Temp=0.1" in variant_results_set
    assert "Model=gpt-3.5, Temp=0.5" in variant_results_set
    assert "Model=gpt-3.5, Temp=0.9" in variant_results_set