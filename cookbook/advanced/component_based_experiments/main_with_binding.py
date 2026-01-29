from typing import Annotated, Callable
from spearmint import Spearmint, Config
from spearmint.configuration import Bind, DynamicValue

from _components import (
    random_search,
    simple_search,
    vector_search,
    noop_rank,
    length_rank,
    alphabetical_rank
)
from spearmint.runner import FunctionResult

# Initialize Spearmint with a single configuration
mint = Spearmint(configs=[
    {
        "search_fn": DynamicValue([random_search, simple_search, vector_search]),
        "rank_fn": DynamicValue([noop_rank, length_rank, alphabetical_rank]),
        "k": DynamicValue(range(2, 4)),
    }
])

@mint.experiment()
def search(
    query: str,
    search_fn: Annotated[Callable, Bind("search_fn")],
    rank_fn: Annotated[Callable, Bind("rank_fn")],
    k: Annotated[int, Bind("k")]
) -> list[str]:
    results = search_fn(query)
    ranked_results = rank_fn(results, k)
    return ranked_results

if __name__ == "__main__":
    # Use the run context manager to handle the experiment execution
    with Spearmint.run(search, await_variants=True) as runner:
        result = runner("not")
        all_results: list[FunctionResult] = []
        all_results.append(result.main_result)
        all_results.extend(result.variant_results)

    expected_search_results = {
        "To be or not to be, that is the question",
        "All that glitters is not gold",
        "Ask not what your country can do for you; ask what you can do for your country",
    }
    evaluations = []
    print(f"Ran {len(all_results)} experiment variants.\n")
    for fn_result in all_results:
        response_eval = {}
        response_eval["result"] = fn_result.result
        for config in fn_result.experiment_case._configs.values():
            if "search_fn" not in config or "rank_fn" not in config:
                continue
            response_eval["search_fn"] = config["search_fn"].__name__
            response_eval["rank_fn"] = config["rank_fn"].__name__
            response_eval["k"] = config["k"]
            break

        precision = len(set(fn_result.result) & expected_search_results) / len(expected_search_results)
        response_eval["precision"] = precision
        
        accuracy = len(set(fn_result.result) & expected_search_results) / len(fn_result.result) if fn_result.result else 0.0
        response_eval["accuracy"] = accuracy

        f1_score = 2 * (precision * accuracy) / (precision + accuracy) if (precision + accuracy) > 0 else 0.0
        response_eval["f1_score"] = f1_score
        evaluations.append(response_eval)

    ordered_evaluations = sorted(evaluations, key=lambda x: x["f1_score"], reverse=True)
    for evaluation in ordered_evaluations:
        print("Search Function:", evaluation["search_fn"])
        print(f"Rank Function: {evaluation['rank_fn']}(k={evaluation['k']})")
        print(f"F1 Score: {evaluation['f1_score']:.2f}, Precision: {evaluation['precision']:.2f}, Accuracy: {evaluation['accuracy']:.2f}")
        print("Result:", evaluation["result"])
        print("-" * 40)