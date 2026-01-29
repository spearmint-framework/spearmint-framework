from spearmint import Config, Spearmint

mint = Spearmint(configs=[{"id": 0}])

def step1(input_str: str) -> str:
    return f"* {input_str} *"

@mint.experiment()
def step2(input_str: str, config: Config) -> str:
    return f"*{config['id']}{input_str}*"

def step3(input_str: str) -> list[str]:
    return input_str.split()

@mint.experiment()
def pipeline(input_str: str) -> list[str]:
    str_with_stars = step1(input_str)
    str_with_config_id = step2(str_with_stars)
    return step3(str_with_config_id)


if __name__ == "__main__":
    with Spearmint.run(pipeline) as runner:
        result = runner("hello world")

    for item in result.main_result.result:
        print(item)

    assert result.main_result.result == ["*0*", "hello", "world", "**"]