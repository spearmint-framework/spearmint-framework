import asyncio

from spearmint import Config, Spearmint

mint = Spearmint(configs=[{"id": 0}])

async def step3point5() -> str:
    await asyncio.sleep(0.1)
    return "==3.5=="

@mint.experiment()
async def step3(a: str, b: str, config: Config) -> str:
    marker = await step3point5()
    return f"{config['id']}-{a} {config['id']}-{b} {marker}"

if __name__ == "__main__":
    async def main() -> None:
        async with Spearmint.arun(step3) as runner:
            results = await runner("step1", "step2")
        print(results.main_result.result)

    asyncio.run(main())
