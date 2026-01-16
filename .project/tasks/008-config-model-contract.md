# Clarify config model contract

## Overview
`Config` is a RootModel over dict, but binding logic accepts any `BaseModel` or `Config` with different behaviors. This implicit contract can surprise users and complicate future evolution.

## Relevant code
- [src/spearmint/configuration/config.py](src/spearmint/configuration/config.py)
- [src/spearmint/experiment_function.py](src/spearmint/experiment_function.py)

## Solution options
1. Restrict binding to `Config` only and require explicit conversion for other models.
2. Support arbitrary `BaseModel` but require a well-defined interface or protocol for extraction.
3. Add a `ConfigAdapter` type to normalize access to dict-like and model-like configs.

## Recommendation
Option 3. It avoids breaking existing behavior while making the contract explicit and testable.