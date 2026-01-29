from spearmint import Config, Spearmint

# Nested experiments allow you to have experiments within experiments.
# This is useful when a subroutine also has configuration options.

mint = Spearmint()

@mint.experiment(configs=[
    {"multiplier": 10},
    {"multiplier": 0},
])
def inner(num: int, config: Config) -> int:
    return num * config["multiplier"]

@mint.experiment(configs=[
    {"addition": 10},
    {"addition": 0},
])
def outer(value: int, config: Config) -> str:
    inner_result = inner(value)
    outer_result = config["addition"] + inner_result
    if outer_result >= 30:
        return f"High:{outer_result}"
    elif outer_result > 10:
        return f"Medium:{outer_result}"
    elif outer_result > 0:
        return f"Low:{outer_result}"
    else:
        return f"Zero:{outer_result}"

if __name__ == "__main__":
    with Spearmint.run(outer, await_variants=True) as runner:
        results = runner(2)

    outer_config_id = results.main_result.experiment_case.get_config_id(outer.__qualname__)
    inner_config_id = results.main_result.experiment_case.get_config_id(inner.__qualname__)
    outer_config = results.main_result.experiment_case._configs[outer_config_id]
    inner_config = results.main_result.experiment_case._configs[inner_config_id]
    print(f"(Main) [mult:{inner_config['multiplier']}|add:{outer_config['addition']}] {results.main_result.result}")
    assert results.main_result.result == "High:30"

    expected_variants = {
        "Medium:20",
        "Low:10",
        "Zero:0",
    }
    for variant in results.variant_results:
        outer_config_id = variant.experiment_case.get_config_id(outer.__qualname__)
        inner_config_id = variant.experiment_case.get_config_id(inner.__qualname__)
        outer_config = variant.experiment_case._configs[outer_config_id]
        inner_config = variant.experiment_case._configs[inner_config_id]
        print(f"(Variant) [mult:{inner_config['multiplier']}|add:{outer_config['addition']}] {variant.result}")
        assert variant.result in expected_variants
        expected_variants.remove(variant.result)