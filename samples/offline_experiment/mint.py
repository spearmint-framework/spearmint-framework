import argparse
import asyncio
from collections.abc import Callable
from pprint import pprint
from typing import Any

from config import (
    MyConfig,  # noqa: F401
    my_dynamic_generator_config,  # noqa: F401
    my_dynamic_list_config,  # noqa: F401
    my_dynamic_range_config,  # noqa: F401
)

from spearmint import Spearmint
from spearmint.core.branch import BranchContainer
from spearmint.config import Config as DefaultMintConfig
from spearmint.strategies import (
    MultiBranchStrategy,
    RoundRobinStrategy,
    ShadowStrategy,
    SingleConfigStrategy,
)

mint = Spearmint(
    # Uncomment exactly one of these strategies to see how it behaves.
    strategy=SingleConfigStrategy,  # Single branch execution (default)
    # strategy=ShadowStrategy,      # Single branch execution (all other configs run in the background)
    # strategy=MultiBranchStrategy, # Multi-branch execution (all configs run in parallel and returned to caller)
    # strategy=RoundRobinStrategy,  # Single branch execution (configs selected in round-robin fashion)
    #
    #
    # Uncomment one or more of these configurations to
    # see how Spearmint handles the different types.
    configs=[
        # {"id": 1},  # Simple python dict config
        my_dynamic_list_config,  # dict with expandable dynamic value: list
        # my_dynamic_range_config, # dict with expandable dynamic value: range
        # my_dynamic_generator_config, # dict with expandable dynamic value: generator
        # "config/config0.yaml", # YAML config file path string
        # Path("config/config1.yaml"), # YAML config file path object
        # "config/", # Directory with YAML config files
    ],
)


def step1(input_str: str = "step1") -> str:
    return input_str


def step2(input_str: str = "step2") -> str:
    return input_str


def step4(c: str) -> list[str]:
    return c.split()


def step5(item: str) -> str:
    return f"final result for {item}"


@mint.experiment()
def step3(a: str, b: str, config: DefaultMintConfig) -> str | BranchContainer:
    return f"{config['id']}-{a} {config['id']}-{b}"


# Decorator binds default Config model to the config parameter
@mint.experiment()
async def async_step3(a: str, b: str, config: DefaultMintConfig) -> str | BranchContainer:
    await asyncio.sleep(0.1)
    return f"{config['id']}-{a} {config['id']}-{b}"


# Decorator binds custom MyConfig model to the config parameter
@mint.experiment(bindings={MyConfig: ""})
def step3_default(a: str, b: str, config: MyConfig) -> str | BranchContainer:
    return f"{config.id}-{a} {config.id}-{b}"


@mint.experiment(strategy=SingleConfigStrategy)
def step3_single(a: str, b: str, config: DefaultMintConfig) -> str | BranchContainer:
    return f"{config['id']}-{a} {config['id']}-{b}"


@mint.experiment(strategy=ShadowStrategy)
def step3_shadow(a: str, b: str, config: DefaultMintConfig) -> str | BranchContainer:
    return f"{config['id']}-{a} {config['id']}-{b}"


@mint.experiment(strategy=RoundRobinStrategy)
def step3_round_robin(a: str, b: str, config: DefaultMintConfig) -> str | BranchContainer:
    return f"{config['id']}-{a} {config['id']}-{b}"


@mint.experiment(strategy=MultiBranchStrategy)
def step3_multi(a: str, b: str, config: DefaultMintConfig) -> str | BranchContainer:
    return f"{config['id']}-{a} {config['id']}-{b}"


def main(step1_input: str, step2_input: str, example: str) -> Any:
    step3_map: dict[str, Callable[[str, str], Any]] = {
        "default": step3_default,
        "single": step3_single,
        "shadow": step3_shadow,
        "roundrobin": step3_round_robin,
        # lambda to allow calling async function in sync context
        "async": lambda a, b: asyncio.run(async_step3(a, b)),
    }
    if example in step3_map:
        print("############################################")
        print(f"# Running single branch with {example.capitalize()} Strategy")
        print(f"# step1_input: {step1_input}, step2_input: {step2_input}")
        print("############################################")
        a = step1(step1_input)
        b = step2(step2_input)
        c = step3_map[example](a, b)
        d = step4(str(c))

        results = []
        for item in d:
            results.append(step5(item))

        print(results, end="\n\n")
        return results

    if example == "multi":
        print("############################################")
        print("# Running multi-branch with MultiBranch Strategy")
        print(f"# step1_input: {step1_input}, step2_input: {step2_input}")
        print("############################################")
        a = step1(step1_input)
        b = step2(step2_input)
        branch_container: BranchContainer = step3_multi(a, b)

        branches = {}
        for branch in branch_container:
            d = step4(branch.output)
            results = []
            for item in d:
                results.append(step5(item))
            branches[branch.config_id] = results

        return branches


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--step1-input", "-s1", default="step1")
    parser.add_argument("--step2-input", "-s2", default="step2")
    parser.add_argument(
        "--example",
        "-e",
        default="default",
        choices=["single", "shadow", "roundrobin", "multi", "default", "async"],
    )
    args = parser.parse_args()

    results = mint.run(
        main,
        dataset=[
            {
                "step1_input": args.step1_input,
                "step2_input": args.step2_input,
                "example": args.example,
            },
            {"step1_input": "foo", "step2_input": "bar", "example": args.example},
        ],
    )

    # results = mint.run(
    #     main,
    #     dataset="samples/offline_experiment/data/step_input.jsonl",
    # )

    pprint(results, indent=2)
