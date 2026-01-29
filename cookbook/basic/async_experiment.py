import asyncio

from spearmint import Config, Spearmint

mint = Spearmint(
    configs=[
        {"id": "fast", "sleep": 0.1},
        {"id": "slow", "sleep": 0.3},
    ]
)

@mint.experiment()
async def fetch_data(url: str, config: Config) -> str:
    print(f"[{config['id']}] Fetching {url}...")
    await asyncio.sleep(config['sleep'])
    return f"Data from {config['id']}"

async def main():
    # TODO: rename await_variants to await_variants
    async with Spearmint.arun(fetch_data, await_variants=True) as runner:
        results = await runner("http://example.com")

    print(f"Main result: {results.main_result.result}")
    for variant in results.variant_results:
        print(f"Variant result: {variant.result}")

if __name__ == "__main__":
    asyncio.run(main())
