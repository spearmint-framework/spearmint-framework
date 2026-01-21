# Reduce reliance on function __qualname__ keys

## Overview
Registry lookup uses `func.__qualname__` as the key. That couples behavior to function naming and makes tests, wrapping, or nested definitions brittle.

## Relevant code
- [src/spearmint/experiment_function.py](src/spearmint/experiment_function.py)
- [src/spearmint/spearmint.py](src/spearmint/spearmint.py)

## Solution options
1. Use the function object identity as the key, not `__qualname__`.
2. Use a stable `ExperimentId` generated and attached at registration time.
3. Keep `__qualname__` but add a fallback map for wrapped functions via `inspect.unwrap`.

## Recommendation
Option 1. It is simplest and avoids naming collisions. Option 2 is viable if you need serialization or persistence across runs.