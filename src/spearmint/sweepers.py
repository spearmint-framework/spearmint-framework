from typing import Any, List


class ListSweeper:
    def __call__(self, *args) -> List[Any]:
        """Create a list of values for parameter sweeps.
        
        Args:
            *args: Values to include in the list
            
        Returns:
            List of the provided values
        """
        return list(args)

class RangeSweeper:
    def __call__(self, start: float, stop: float, step: float = 1.0) -> List[float]:
        """Create a range of values for parameter sweeps.
        
        Args:
            start: The starting value
            stop: The ending value (inclusive)
            step: The step size
            
        Returns:
            List of values from start to stop with the given step size
        """
        return range(start, stop, step)