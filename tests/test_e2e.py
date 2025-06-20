import pytest

import spearmint as mint

class MyClient:
    """A mock client class for demonstration purposes."""
    def __init__(self, name: str, value: int = 10) -> None:
        self.name = name
        self.value = value

    def subtract(self, number: int, offset: int = 0) -> int:
        return number - self.value + offset  # Example processing logic

@mint.add_experiment()
def my_experiment(num: int, *, multiplier: int) -> int:
    """A simple experiment function that returns ints."""
    result = None
    if num < 0:
         result = -num
    else:
        result = num * multiplier
    
    print(f"Experiment run with num={num}, multiplier={multiplier}, result={result}")
    return result

@mint.add_experiment()
def chained_experiment(num: int) -> int:
    """A chained experiment that uses the add_value and multiply_value tools."""
    step1 = add_value(num)
    step2 = multiply_value(step1)
    step3 = some_tool(step2)
    print(f"Chained experiment run with num={num}, step1={step1}, step2={step2}, step3={step3}")
    return step3

@mint.configurable("add_value")
def add_value(number: int, *, additional_value: int) -> int:
    return number + additional_value

@mint.configurable("multiply_value")
def multiply_value(number: int, *, multiplier: int) -> int:
    return number * multiplier

@mint.configurable("some_tool")
def some_tool(number: int, *, client: MyClient) -> int:
    return client.subtract(number)

class ExactMatchEvaluator:
    """A custom evaluator that checks if the response matches the expected value."""
    def __init__(self, expected_key: str = "expected", response_key: str = "response") -> None:
        """
        Initialize the ExactMatchEvaluator.
        
        Args:
            column_mapping: A dictionary mapping dataset columns to experiment inputs.
            expected: The expected response value.
        """
        self.expected_key = expected_key
        self.response_key = response_key

    def __call__(self, *args, **kwargs) -> dict:
        expected = kwargs.get(self.expected_key)
        response = kwargs.get(self.response_key)
        if expected is not None and response is not None:
            if expected == response:
                print(f"Exact match: {expected} == {response}")
                return {"exact_match": True}
            else:
                print(f"Mismatch: {expected} != {response}")
                return {"exact_match": False}
        else:
            print("Expected or response is None")
        return {}


@pytest.mark.asyncio
async def test_e2e():
    """Test that hypothesis.run calls the experiment function exactly once."""
    # Empty config yaml
    mint.configure("./tests/data/config.yaml")
    
    # {"number": -1, "expected": 1}
    # {"number": 2, "expected": 4}
    # {"number": -2, "expected": 2}
    # {"number": 3, "expected": 6}
    # {"number": -4, "expected": 4}
    # {"number": 1, "expected": 2}
    # {"number": 0, "expected": 0}
    # {"number": 5, "expected": 10}
    # {"number": -3, "expected": 3}
    # {"number": 4, "expected": 8}
    mint.load_dataset("./tests/data/dataset.jsonl")

    # define input mapping
    mint.inputs({
        "num": "number",
    })
    mint.add_evaluator(ExactMatchEvaluator())
    mint.add_service(MyClient)

    runs = await mint.run("my_experiment", config={
        "multiplier": mint.vary([1,2])
    })

    assert len(runs) == 2
    
    # Sort runs by multiplier to ensure consistent test ordering
    runs.sort(key=lambda x: x["config"]["multiplier"])
    
    for run in runs:
        print(f"\n\nRun config: {run['config']}")
        for line in run["dataset"]:
            print(f"Dataset line: {line}")

    # Test run with multiplier = 1
    assert runs[0]["config"] == {"multiplier": 1}
    assert runs[0]["dataset"] == [
        {"number":-1, "expected": 1, "response": 1, "ExactMatchEvaluator": { "exact_match": True}}, # abs(-1) = 1
        {"number":2, "expected": 4, "response": 2, "ExactMatchEvaluator": { "exact_match": False}},  # 2 * 1 = 2
        {"number":-2, "expected": 2, "response": 2, "ExactMatchEvaluator": { "exact_match": True}}, # abs(-2) = 2
        {"number":3, "expected": 6, "response": 3, "ExactMatchEvaluator": { "exact_match": False}},  # 3 * 1 = 3
        {"number":-4, "expected": 4, "response": 4, "ExactMatchEvaluator": { "exact_match": True}}, # abs(-4) = 4
        {"number":1, "expected": 2, "response": 1, "ExactMatchEvaluator": { "exact_match": False}},   # 1 * 1 = 1
        {"number":0, "expected": 0, "response": 0, "ExactMatchEvaluator": { "exact_match": True}},   # 0 * 1 = 0
        {"number":5, "expected": 10, "response": 5, "ExactMatchEvaluator": { "exact_match": False}},   # 5 * 1 = 5
        {"number":-3, "expected": 3, "response": 3, "ExactMatchEvaluator": { "exact_match": True}}, # abs(-3) = 3
        {"number":4, "expected": 8, "response": 4, "ExactMatchEvaluator": { "exact_match": False}}    # 4 * 1 = 4
    ]
    
    # Test run with multiplier = 2
    assert runs[1]["config"] == {"multiplier": 2}
    assert runs[1]["dataset"] == [
        {"number":-1, "expected": 1, "response": 1, "ExactMatchEvaluator": { "exact_match": True}},    # abs(-1) = 1
        {"number":2, "expected": 4, "response": 4, "ExactMatchEvaluator": { "exact_match": True}},     # 2 * 2 = 4
        {"number":-2, "expected": 2, "response": 2, "ExactMatchEvaluator": { "exact_match": True}},    # abs(-2) = 2
        {"number":3, "expected": 6, "response": 6, "ExactMatchEvaluator": { "exact_match": True}},     # 3 * 2 = 6
        {"number":-4, "expected": 4, "response": 4, "ExactMatchEvaluator": { "exact_match": True}},    # abs(-4) = 4
        {"number":1, "expected": 2, "response": 2, "ExactMatchEvaluator": { "exact_match": True}},     # 1 * 2 = 2
        {"number":0, "expected": 0, "response": 0, "ExactMatchEvaluator": { "exact_match": True}},     # 0 * 2 = 0
        {"number":5, "expected": 10, "response": 10, "ExactMatchEvaluator": { "exact_match": True}},   # 5 * 2 = 10
        {"number":-3, "expected": 3, "response": 3, "ExactMatchEvaluator": { "exact_match": True}},    # abs(-3) = 3
        {"number":4, "expected": 8, "response": 8, "ExactMatchEvaluator": { "exact_match": True}}      # 4 * 2 = 8
    ]

    chained_runs = await mint.run("chained_experiment", config={
        "add_value": {
            "additional_value": 0
        },
        "multiply_value": {
            "multiplier": 1
        },
        "some_tool": {
            "offset": 10,
        }
    })