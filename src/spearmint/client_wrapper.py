from typing import Any, Callable, Dict, TypeVar, cast, get_type_hints, List, Union
from spearmint import ConfigDict
import copy

T = TypeVar("T")

class ClientWrapper:
    """
    A wrapper class that forwards method calls to an underlying client instance.
    This is useful for wrapping API clients like the OpenAI client.
    
    The wrapper allows for:
    - Pre and post-processing of calls
    - Logging or monitoring of API usage
    - Configuration management
    - Adding retry or error handling logic
    - Handling Dynamic values that should be evaluated at call time
    """
    
    def __init__(self, class_type: T, config: ConfigDict):
        """
        Initialize the ClientWrapper with a client instance.
        
        :param class_type: The class type to instantiate.
        :param config: Configuration dictionary.
        """
        class_name = class_type.__name__  # Changed from class_type.__class__.__name__
        self.config = config[class_name]
        self.client_config = {k: v for k, v in self.config.items() if k != "methods"}
        self._client : T = class_type(**self.client_config)
        self.methods_config = self.config.get("methods", {})
        self._method_cache = {}
    
    def __getattr__(self, name: str) -> Callable:
        """
        Forward attribute access to the underlying client.
        If the attribute is a method, wrap it to provide additional functionality.
        
        :param name: The name of the attribute to access.
        :return: The wrapped method or attribute from the underlying client.
        """
        # First check if we've already cached this method
        if name in self._method_cache:
            return self._method_cache[name]
        
        # Get the attribute from the client
        attr = getattr(self._client, name)
        
        # If it's a method, wrap it
        if callable(attr):
            wrapped_method = self._wrap_method(name, attr)
            # Cache the wrapped method
            self._method_cache[name] = wrapped_method
            return wrapped_method
        
        # If it's not a method, return it directly
        return attr
    
    def __dir__(self):
        """Expose the wrapped client's attributes for autocomplete."""
        return sorted(dir(self._client))
    
    def _resolve_dynamic_values(self, config: Any, kwargs: dict) -> Any:
        """
        Recursively resolves any Dynamic values in the configuration.
        
        :param config: The configuration to process.
        :return: The configuration with Dynamic values resolved.
        """
        if hasattr(config, "__class__") and config.__class__.__name__ == "Dynamic":
            # This is a Dynamic value, return its content
            return kwargs.pop(config.key)
        
        if hasattr(config, "__class__") and config.__class__.__name__ == "DynamicFn":
            # This is a Dynamic function, call it with the provided arguments
            dynamic_fn = cast(Callable, config.fn)
            dynamic_args = [self._resolve_dynamic_values(arg, kwargs) for arg in config.args]
            dynamic_kwargs = {k: self._resolve_dynamic_values(v, kwargs) for k, v in config.kwargs.items()}
            return dynamic_fn(*dynamic_args, **dynamic_kwargs)
        
        if isinstance(config, dict):
            # Process dictionary
            return {k: self._resolve_dynamic_values(v) for k, v in config.items()}
        elif isinstance(config, list):
            # Process list
            return [self._resolve_dynamic_values(item) for item in config]
        
        # For all other types, return as is
        return config
    
    def _wrap_method(self, name: str, method: Callable) -> Callable:
        """
        Wrap a method of the underlying client to add custom behavior.
        
        :param name: The name of the method.
        :param method: The method to wrap.
        :return: The wrapped method.
        """
        method_config = self.methods_config.get(name, {})

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            # Create a deep copy of the method config to avoid modifying the original
            current_config = copy.deepcopy(method_config)
            
            # Resolve any Dynamic values in the configuration
            resolved_config = self._resolve_dynamic_values(current_config, kwargs)
            
            # Update with any kwargs provided in the call
            resolved_config.update(kwargs)
            
            # Call the underlying method with the resolved configuration
            result = method(*args, **resolved_config)
            
            # Post-processing logic can be added here
            # Example: transforming results, error handling
            
            return result
        
        # Set the name and docstring of the wrapped method
        wrapped.__name__ = method.__name__
        wrapped.__doc__ = method.__doc__
        
        return wrapped