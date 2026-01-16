# Separate config binding from ExperimentFunction

## Overview
`ExperimentFunction` handles type inspection, config binding, and injection. This merges separate concerns and makes it hard to extend binding behavior.

## Relevant code
- [src/spearmint/experiment_function.py](src/spearmint/experiment_function.py)

## Solution options
1. Extract a `ConfigBinder` service that handles annotation parsing and injection.
2. Use a strategy interface for binding so different binding rules can be swapped.
3. Keep in place but refactor into private helper classes within the same module.

## Recommendation
Option 1. It yields a clear surface for tests and for future binding rules without expanding `ExperimentFunction` further.