from pathlib import Path

from spearmint import Config, Spearmint

# You can load configs from YAML files or directories of YAML files.

BASE_DIR = Path(__file__).parent

# Initialize Spearmint with YAML config files
mint = Spearmint(
    configs=[
        BASE_DIR / "config" / "config0.yaml", # id: 10
        BASE_DIR / "config" / "config1.yaml", # id: 20
        BASE_DIR / "config" / "config2.yaml", # id: 30
    ]
)

@mint.experiment()
def handle(value: str, config: Config) -> str:
    return f"{value}_{config['id']}"

if __name__ == "__main__":
    with Spearmint.run(handle, await_variants=True) as runner:
        results = runner("yaml")
        print(f"Main Result: {results.main_result.result}")
        assert results.main_result.result == "yaml_10"
        variant_results = [variant.result for variant in results.variant_results]
        assert "yaml_20" in variant_results
        assert "yaml_30" in variant_results
