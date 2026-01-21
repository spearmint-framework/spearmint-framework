# Remove or wire in unused branch_strategy

## Overview
`branch_strategy` is part of the public API but is not used in execution. This is dead surface area and creates confusion and future debt.

## Relevant code
- [src/spearmint/spearmint.py](src/spearmint/spearmint.py)

## Solution options
1. Implement the strategy in `ExperimentRunner` or `ExperimentFunction` so it controls selection of main and variant configs.
2. Remove `branch_strategy` from public APIs and reintroduce when the strategy is actually used.
3. Deprecate it with warnings, then remove in a future release.

## Recommendation
Option 2, unless a short-term implementation is already planned. If so, prefer option 1 and add tests that exercise strategy behavior.