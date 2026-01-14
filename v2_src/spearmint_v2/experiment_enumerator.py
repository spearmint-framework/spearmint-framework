from collections import defaultdict
from collections.abc import Callable
from typing import Any


class ExperimentEnumerator:
    
    def __init__(self) -> None:
        self.experiment_fns = defaultdict(dict[str, dict])
        self.called_fns = defaultdict(list[str])

    def register_experiment(
            self,
            fn: Callable,
            main_handler: Callable[..., Any],
            background_handler: Callable[..., Any],
            configs: list[Any] = []
        ) -> None:
        self._update_details(fn, main_handler, background_handler, configs=configs)
        self._update_called_fns(fn)

    def _update_called_fns(self, fn: Callable) -> None:
        # Get the functions called within the experiment function
        import ast
        import inspect

        source = inspect.getsource(fn)
        tree = ast.parse(source)
        called_fns = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        for called_fn in called_fns:
            self.called_fns[called_fn].append(fn.__name__)

    def _update_details(self, fn: Callable, main_handler: Callable[..., Any], background_handler: Callable[..., Any], configs: list[Any]) -> None:
        details = {
            "main_handler": main_handler,
            "background_handler": background_handler,
            "configs": configs,
        }
        if fn.__name__ in self.called_fns:
            called_by_fns = self.called_fns[fn.__name__]
            for caller in called_by_fns:
                calls = self.experiment_fns[caller].get("calls", {})
                if fn.__name__ not in calls:
                    calls[fn.__name__] = details
                    self.experiment_fns[caller]["calls"] = calls

        self.experiment_fns[fn.__name__] = details

    def get_config_paths(self, fn_name: str) -> list[dict[str, str]]:
        """Get all config paths for a given experiment function."""
        fn_details = self.experiment_fns.get(fn_name)
        if not fn_details:
            raise ValueError(f"No experiment found for function '{fn_name}'")
        calls = fn_details.get("calls", {})
        config_paths = []

        config_paths.append(fn_details["main_handler"](fn_details.get("configs", [])))
        config_paths.extend(fn_details["background_handler"](fn_details.get("configs", [])))
        
        for called_fn_name in calls.keys():
            config_paths.extend(self.get_config_paths(called_fn_name))

        return config_paths