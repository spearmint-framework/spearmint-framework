"""Core module for the Spearmint framework.

This module contains the main Spearmint class that serves as the central point for 
registering experiments, hypotheses, factors and running the framework.
"""
import asyncio
import itertools
from typing import Any, Callable, Dict, List, Optional, Type, Union
import functools

class Spearmint:
    """Main class for the Spearmint framework.
    
    This class handles registration and execution of experiments,
    hypotheses, and factors.
    """
    
    def __init__(self):
        """Initialize the Spearmint instance."""
        self._experiments = {}
        self._hypotheses = {}
        self._factors = {}
    
    def register_experiment(self, 
                           name: str, 
                           data: str, 
                           inputs: Dict[str, Dict[str, Any]], 
                           outputs: Dict[str, Dict[str, Any]], 
                           evaluators: List[Any]) -> None:
        """Register an experiment with the framework.
        
        Args:
            name: The name of the experiment
            data: Path to the ground truth data
            inputs: Input schema definitions
            outputs: Output schema definitions
            evaluators: List of evaluator functions
        """
        self._experiments[name] = {
            'data': data,
            'inputs': inputs,
            'outputs': outputs,
            'evaluators': evaluators
        }
    
    def hypothesis(self, func: Callable) -> Callable:
        """Decorator to register a function as a hypothesis.
        
        Args:
            func: The function to register as a hypothesis
            
        Returns:
            The original function unchanged
        """
        self._hypotheses[func.__name__] = func
        return func
    
    def factor(self, func: Callable) -> Callable:
        """Decorator to register a function as a factor.
        
        Args:
            func: The function to register as a factor
            
        Returns:
            The original function unchanged
        """
        self._factors[func.__name__] = func
        return func
    
    def run(self, experiment: str, hypothesis: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run an experiment with the given hypothesis and configuration.
        
        Args:
            experiment: The name of the experiment to run
            hypothesis: The name of the hypothesis to test
            config: Configuration parameters for the run
            
        Returns:
            Results of the experiment
        """
        if experiment not in self._experiments:
            raise ValueError(f"Experiment '{experiment}' not found")
            
        if hypothesis not in self._hypotheses:
            raise ValueError(f"Hypothesis '{hypothesis}' not found")
        
        configurations = self._generate_configurations(config)
        
        data = self._experiments[experiment]['data']
        inputs = self._experiments[experiment]['inputs']
        outputs = self._experiments[experiment]['outputs']
        evaluators = self._experiments[experiment]['evaluators']

        hypo_func = self._hypotheses[hypothesis]
        
        results = {}
        for config in self.configurations:
            # mlflow.start_run(experiment_id=experiment)
            for data_item in data:
                results.get(config.id, []).append(hypo_func(data_item, config))
            # mlflow.end_run()

        for result in results:
            for evaluator in evaluators:
                evaluator(result, outputs)
        
        # This is a placeholder for demonstration
        return {"status": "executed", "experiment": experiment, "hypothesis": hypothesis}

    def _generate_configurations(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate configurations for the experiment based on the provided config.
        
        Args:
            config: Configuration parameters
            
        Returns:
            List of generated configurations
        """
        sweepers = self._find_sweepers(config)
        values = []
        configurations = []
        
        for sweeper in sweepers:
            vals = sweeper['sweeper']()
            values.append([{"keys": sweeper['parent_keys'], "value": val} for val in vals])

        # use itertools to generate all combinations of the sweeper values
        for combo in itertools.product(*values):
            config_copy = config.copy()
            for item in combo:
                keys = item['keys']
                value = item['value']
                # Traverse the config dictionary to set the value
                d = config_copy
                for key in keys[:-1]:
                    d = d.setdefault(key, {})
                d[keys[-1]] = value
            configurations.append(config_copy)

        

    def _find_sweepers(self, config: Dict[str, Any], parent_keys: list = []) -> List[Dict[str, Any]]:
        """Find all sweepers in the configuration.
        
        Args:
            config: Configuration parameters
            
        Returns:
            List of found sweepers
        """
        sweepers = []
        for key, value in config.items():
            if isinstance(value, (ListSweeper, RangeSweeper)):
                keys = [key].extend(parent_keys)
                sweepers.append({"sweeper": value, "parent_keys": keys})
            elif isinstance(value, dict):
                parent_keys.append(key)
                nested_sweepers = self._find_sweepers(value, parent_keys)
                if nested_sweepers:
                    sweepers.extend(nested_sweepers)
        return sweepers
        


class ExperimentRuntime:
    async def __call__(self, *args, **kwargs):
        pre_run_tasks = []
        for pre_run_handler in self._pre_run_handlers:
            if isinstance(pre_run_handler, Callable):
                pre_run_tasks.append(pre_run_handler(*args, **kwargs))
            else:
                raise TypeError(f"Pre-run handler {pre_run_handler} is not callable")
        if pre_run_tasks:
            await asyncio.gather(*pre_run_tasks)

        results = []
        for data_item in self._data:
            results.append(self._process_data_item(data_item))

        if results:
            self.results = await asyncio.gather(*results)

        post_run_tasks = []
        for post_run_handler in self._post_run_handlers:
            if isinstance(post_run_handler, Callable):
                post_run_tasks.append(post_run_handler(*args, **kwargs))
            else:
                raise TypeError(f"Post-run handler {post_run_handler} is not callable")
        if post_run_tasks:
            await asyncio.gather(*post_run_tasks)

class BasicRunner(ExperimentRuntime):
    """Basic runner for executing experiments in the Spearmint framework."""
    
    def __init__(self, data: List[Any], pre_run_handlers: List[Callable] = [], post_run_handlers: List[Callable] = []):
        """Initialize the BasicRunner with data and handlers.
        
        Args:
            data: List of data items to process
            pre_run_handlers: List of pre-run handler functions
            post_run_handlers: List of post-run handler functions
        """
        self._data = data
        self._pre_run_handlers = pre_run_handlers
        self._post_run_handlers = post_run_handlers
        self.results = []

    def _process_data_item(self, data_item: Any) -> Any:
        """Process a single data item.
        
        Args:
            data_item: The data item to process
            
        Returns:
            Processed result of the data item
        """
        # Placeholder for actual processing logic
        return data_item  # In a real implementation, this would be replaced with actual processing logic