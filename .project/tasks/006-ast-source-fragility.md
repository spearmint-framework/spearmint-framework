# Isolate AST-based inner call discovery

## Overview
Inner call discovery uses `inspect.getsource` and AST parsing. This fails for dynamically defined functions, decorated functions, or interactive environments, and it is embedded in core execution.

## Relevant code
- [src/spearmint/experiment_function.py](src/spearmint/experiment_function.py)

## Solution options
1. Move AST parsing behind an optional feature flag and allow a manual registration path for nested experiments.
2. Replace AST parsing with explicit API calls to register inner experiments at definition time.
3. Keep parsing but add robust error handling and clear fallbacks to disable nested behavior.

## Recommendation
Option 2 if you can tolerate explicit registration. Otherwise option 1 with a clean fallback path.