from typing import Annotated

from spearmint import Config, Spearmint
from spearmint.configuration import Bind

mint = Spearmint(
    configs=[
        {
            "bound": {
                "config": {
                    "id": "my_bound_config",
                }
            }
        }
    ]
)

@mint.experiment()
def process(value: str, config: Annotated[Config, Bind("bound.config")]) -> str:
    return f"{value}_{config['id']}"

if __name__ == "__main__":
    with Spearmint.run(process) as runner:
        results = runner("test")
        print(results.main_result.result)
