from spearmint import experiment, Config
from spearmint.strategies import ShadowBranchStrategy

@experiment(
    branch_strategy=ShadowBranchStrategy,
    configs=[{"value": 1}, {"value": 10}],
)
def my_nested_fn(x: int, config: Config) -> int:
    return x * config["value"]