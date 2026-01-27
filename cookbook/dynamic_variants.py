from spearmint import Config, Spearmint
from spearmint.configuration import DynamicValue

# Run all generated configs by awaiting background variants.

mint = Spearmint(
    configs=[
        {
            "id": DynamicValue(["a", "b", "c"]),
        }
    ]
)

@mint.experiment()
def show_variant(config: Config) -> str:
    return f"Variant {config['id']}"

if __name__ == "__main__":
    with Spearmint.run(show_variant, await_background_cases=True) as runner:
        results = runner()

    print(f"Main: {results.main_result.result}")
    print("Variants:")
    for variant in results.variant_results:
        print(f"- {variant.result}")
