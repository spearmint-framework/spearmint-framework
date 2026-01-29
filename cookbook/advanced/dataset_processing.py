import json
from pathlib import Path

from spearmint import Config, Spearmint

# This recipe demonstrates how to run an experiment over a dataset of inputs.

mint = Spearmint(configs=[{"id": 0}])

@mint.experiment()
def process_item(base_str: str, config: Config) -> str:
    return f"{base_str}_{config['id']}"

if __name__ == "__main__":
    dataset_path = Path(__file__).parent / "data" / "sample.jsonl"

    with Spearmint.run(process_item) as runner:
        for line in dataset_path.read_text().splitlines():
            record = json.loads(line)
            result = runner(record["base_str"])
            print(f"{result.main_result.result} (expected: {record['expected_output']})")
            assert result.main_result.result == record["expected_output"]

