from typing import Annotated

from spearmint import Config, Spearmint
from spearmint.configuration import Bind

mint = Spearmint(
    configs=[
        {
            "bound": {
                "config": {
                    "my_var": "my_bound_config",
                },
                "my_var": "this is not passed",
            },
            "my_var": "this is not passed"
        }
    ]
)

@mint.experiment()
def process(value: str, config: Annotated[Config, Bind("bound.config")]) -> str:
    return f"{value}_{config['my_var']}"

if __name__ == "__main__":
    with Spearmint.run(process) as runner:
        results = runner("test")
        print(results.main_result.result)
        assert results.main_result.result == "test_my_bound_config"
