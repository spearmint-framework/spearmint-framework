from spearmint import Config, Spearmint

mint = Spearmint(configs=[{"id": 0}])


def step1(input_str: str = "step1") -> str:
    return input_str


def step2(input_str: str = "step2") -> str:
    return input_str


def step4(c: str) -> list[str]:
    return c.split()


def step5(item: str) -> str:
    return f"final result for {item}"


@mint.experiment()
def step3(a: str, b: str, config: Config) -> str:
    return f"{config['id']}-{a} {config['id']}-{b}"


if __name__ == "__main__":
    with Spearmint.run(step3) as runner:
        result = runner(step1("hello"), step2("world"))

    for item in step4(result.main_result.result):
        print(step5(item))
