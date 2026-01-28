import json
from pathlib import Path

from spearmint import Config, Spearmint

# This recipe demonstrates how to run an experiment over a dataset of inputs.

mint = Spearmint(configs=[{"id": 0}])

@mint.experiment()
def process_item(step1_input: str, step2_input: str, config: Config) -> str:
    return f"{config['id']}-{step1_input} {config['id']}-{step2_input}"

if __name__ == "__main__":
    dataset_path = Path(__file__).parent / "data" / "step_input.jsonl"

    with Spearmint.run(process_item) as runner:
        for line in dataset_path.read_text().splitlines():
            record = json.loads(line)
            result = runner(
                step1_input=record["step1_input"],
                step2_input=record["step2_input"],
            )
            print(result.main_result.result)
