"""
Hypothesis module for the Spearmint framework.

This module contains the Hypothesis class, which is the main entrypoint for creating
and running experiments with the Spearmint framework.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union, TYPE_CHECKING
import asyncio
from .config import _generate_configurations

# Import the Experiment type for type hints
if TYPE_CHECKING:
    from .experiment import Experiment

class Hypothesis:
    """
    Hypothesis is the main class for creating and running experiments.
    
    It provides methods for configuring experiments, adding services, and
    running experiments with specific configurations.
    """
    
    def __init__(self) -> None:
        """Initialize a new Hypothesis instance."""
        self._experiments = {}
        self._services = []
        self._config = {}
    
    def configure(self, config_path: str) -> None:
        """
        Configure the hypothesis with settings from a YAML file.
        
        Args:
            config_path: Path to the YAML configuration file.
        """
        pass
    
    def add_service(self, service_class: Type[Any]) -> None:
        """
        Add a service to the hypothesis.
        
        Args:
            service_class: The service class to add.
        """
        pass
    
    def add_experiment(self, experiment: Experiment, name: str) -> None:
        """
        Add an experiment to the hypothesis with a specific name.
        
        Args:
            experiment: The experiment to add.
            name: The name to give the experiment.
        """
        if not isinstance(experiment, Experiment):
            raise TypeError("Expected an instance of Experiment")
        self._experiments[name] = experiment
    
    async def run(self, experiment: "Experiment", config: Dict[str, Any]) -> Any:
        """
        Run an experiment with an optional configuration.
        
        Args:
            experiment: The experiment to run.
            config: Optional configuration to use when running the experiment.
            
        Returns:
            The result of running the experiment.
        """
        experiment_variants = []
        for config in _generate_configurations(config):
            print(f"Running experiment with configuration: {config}")
            # Run the experiment with the provided configuration
            experiment_variants.append(experiment(**config))
            # Process the result as needed

        async_results = await asyncio.gather(*experiment_variants)

        return async_results


    
    def input(self, input_class: Type[Any]) -> None:
        """
        Define the input type for the hypothesis.
        
        Args:
            input_class: The input class/type.
        """
        pass
    
    def output(self, output_class: Type[Any]) -> None:
        """
        Define the output type for the hypothesis.
        
        Args:
            output_class: The output class/type.
        """
        pass
    
    def data(self, data_path: str) -> None:
        """
        Specify a data source for the hypothesis.
        
        Args:
            data_path: Path to the data file.
        """
        pass
