# Remove unused imports to reduce noise

## Overview
Unused imports add noise and create confusion about dependencies and intentions.

## Relevant code
- [src/spearmint/experiment_function.py](src/spearmint/experiment_function.py)
- [src/spearmint/spearmint.py](src/spearmint/spearmint.py)

## Solution options
1. Remove unused imports immediately and enable linting to prevent reintroduction.
2. Add a linter rule in the project config and clean up incrementally.

## Recommendation
Option 1. This is low-risk and improves clarity right away.