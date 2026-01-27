from spearmint import Spearmint, Config
from spearmint.configuration import DynamicValue

# DynamicValue allows you to generate multiple configurations combinatorially.
# This is useful for grid search or parameter sweeping.

configs = [
    {
        # This will expand into 2 values
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        # This will expand into 3 values (0.1, 0.5, 0.9)
        "temperature": DynamicValue([0.1, 0.5, 0.9]),
        "static_param": "always_same",
    }
]
# Total generated configs: 2 * 3 = 6

mint = Spearmint(configs=configs)

@mint.experiment()
def train_model(config: Config) -> str:
    return f"Model={config['model']}, Temp={config['temperature']}"

if __name__ == "__main__":
    print(f"Generated {len(mint.configs)} configurations.")

    with Spearmint.run(train_model) as runner:
        result = runner()
        print(f"Run result (first config): {result.main_result.result}")
