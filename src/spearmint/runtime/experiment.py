"""
Experiment module for the Spearmint framework.

This module contains the Experiment class, which is used to define and configure
experiments that can be run by the Hypothesis class.
"""

import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

# Type variables for better type hints
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class Experiment:
    """
    Experiment class that can be called as a function.
    
    An Experiment is a wrapper around a function that can be configured and run
    with specific parameters and services.
    """
    
    def __init__(self, run_fn: Callable) -> None:
        """Initialize a new Experiment instance."""
        self._run_fn = run_fn
        self._service_fns = {}
        self._config_fns = {}
        self._middleware = []
        self_results: List[dict] = []
        
    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the experiment as a function.
        
        Args:
            *args: Positional arguments to pass to the run function.
            **kwargs: Keyword arguments to pass to the run function.
            
        Returns:
            The result of calling the run function. If the function is a 
            generator, returns the generator object.
        """
        # configured_kwargs = {}

        # # check if the function takes an argument that matches the type of a registered service in self._service_fns
        # if hasattr(self._run_fn, '__annotations__'):
        #     annotations = self._run_fn.__annotations__
        #     for param_name, param_type in annotations.items() if annotations else []:
        #         if param_type.__name__ in self._service_fns:
        #             # If the parameter type matches a service, configure it
        #             configured_kwargs[param_name] = self._service_fns[param_type.__name__]

        if inspect.isgeneratorfunction(self._run_fn):
            return await self._call_generator(*args, **kwargs)
        else:
            return await self._call_function(*args, **kwargs)
    
    async def _call_function(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the run function as a regular function.
        
        Args:
            *args: Positional arguments to pass to the run function.
            **kwargs: Keyword arguments to pass to the run function.
            
        Returns:
            The result of calling the run function.
        """
        # if the function is not a coroutine, we need to run it in an event loop
        if not asyncio.iscoroutinefunction(self._run_fn):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, functools.partial(self._run_fn, *args, **kwargs))
        # if the function is a coroutine, we can call it directly
        else:
            return await self._run_fn(*args, **kwargs)
    
    def _call_generator(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the run function as a generator function.
        
        Args:
            *args: Positional arguments to pass to the run function.
            **kwargs: Keyword arguments to pass to the run function.
            
        Returns:
            A generator object that yields results from the run function.
        """
        gen = self._run_fn(*args, **kwargs)
        if not inspect.isgenerator(gen):
            raise TypeError("The run function must be a generator function.")
        
        # Run the generator until it yields a value
        yielded_value = None
        while True:
            try:
                yielded_value = next(gen)
                if isinstance(yielded_value, Callable):
                    gen.send(yielded_value(**self._config_fns.get(yielded_value.__name__, {})))
            except StopIteration as e:
                break

        return yielded_value
    

def experiment(func: F, name: str) -> Experiment:
    """
    Decorator to create an Experiment from a function.
    
    This decorator creates a new Experiment instance and sets the provided
    function as its run function. The returned Experiment instance can be
    called like the original function.
    
    Args:
        func: The function to wrap in an Experiment.
        
    Returns:
        An Experiment instance that wraps the provided function.
    """
    exp = Experiment(func)
    return exp