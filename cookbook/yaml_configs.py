from pathlib import Path

from spearmint import Config, Spearmint

# You can load configs from YAML files or directories of YAML files.

BASE_DIR = Path(__file__).parent

mint = Spearmint(
    configs=[
        BASE_DIR / "config" / "config0.yaml",
        BASE_DIR / "config" / "config1.yaml",
        BASE_DIR / "config" / "config2.yaml",
    ]
)

@mint.experiment()
def handle(value: str, config: Config) -> str:
    return f"{value}_{config['id']}"

if __name__ == "__main__":
    with Spearmint.run(handle) as runner:
        results = runner("yaml")
        print(results.main_result.result)
