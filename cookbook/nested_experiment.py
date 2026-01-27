from spearmint import Config, Spearmint

# Nested experiments allow you to have experiments within experiments.
# This is useful when a subroutine also has configuration options.

inner_mint = Spearmint(
    configs=[
        {"id": "inner_a"},
        {"id": "inner_b"},
    ]
)

@inner_mint.experiment()
def inner(value: str, config: Config) -> str:
    return f"{value}_{config['id']}"

outer_mint = Spearmint(
    configs=[
        {"id": "outer_a"},
        {"id": "outer_b"},
    ]
)

@outer_mint.experiment()
def outer(value: str, config: Config) -> str:
    inner_result = inner(value)
    return f"{config['id']}|{inner_result}"

if __name__ == "__main__":
    with Spearmint.run(outer, await_background_cases=True) as runner:
        results = runner("test")

    print(f"Main: {results.main_result.result}")
    print("Variants:")
    for variant in results.variant_results:
        print(f"- {variant.result}")
