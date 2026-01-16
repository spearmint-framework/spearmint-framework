# Explicit lifecycle for registry and contextvars

## Overview
Global mutable registry and contextvars are created at import time. This makes behavior implicit, complicates tests, and makes multiple independent instances awkward.

## Relevant code
- [src/spearmint/spearmint.py](src/spearmint/spearmint.py)
- [src/spearmint/experiment_function.py](src/spearmint/experiment_function.py)

## Solution options
1. Store the registry and runner contextvars as instance state on `Spearmint` and pass them explicitly where needed.
2. Introduce a small registry module with an explicit `initialize()` / `reset()` API for tests and allow injection for advanced users.
3. Keep globals but add a test helper to reset them and document constraints.

## Recommendation
Option 1, unless you need cross-instance sharing. If shared registry is required, adopt option 2 with explicit lifecycle control.