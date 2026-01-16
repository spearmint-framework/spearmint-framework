# Split monolithic module responsibilities

## Overview
The main module is handling the decorator API, context management, orchestration, sync/async bridging, and global registry wiring in one place. This concentrates multiple responsibilities and makes it hard to test or change parts independently.

## Relevant code
- [src/spearmint/spearmint.py](src/spearmint/spearmint.py)

## Solution options
1. Create separate modules for runner, contextvars, and decorator API. For example: `runner.py`, `context.py`, `decorators.py`, and keep `Spearmint` as a thin façade.
2. Move `ExperimentRunner` and contextvars into a new module and keep the decorator in spearmint.py, reducing but not eliminating coupling.
3. Convert `Spearmint` into a package-level namespace and expose functions from submodules via `__init__.py` to minimize import churn.

## Recommendation
Option 1. It yields clear ownership boundaries, better unit-test scoping, and avoids future tangles as features expand.