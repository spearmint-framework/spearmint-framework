# Remove mutable default argument for configs

## Overview
`ExperimentFunction` uses a mutable default for `configs`, which can lead to shared state across instances.

## Relevant code
- [src/spearmint/experiment_function.py](src/spearmint/experiment_function.py)

## Solution options
1. Change the default to `None` and create a list inside the initializer.
2. Keep the list but deep-copy it at initialization time.

## Recommendation
Option 1. It is the standard safe pattern and avoids surprising shared state.