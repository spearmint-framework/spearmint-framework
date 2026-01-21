# Remove reliance on Pydantic private API

## Overview
`DynamicValue` imports a private Pydantic internal module for schema generation. This is likely to break across Pydantic versions.

## Relevant code
- [src/spearmint/configuration/dynamic_value.py](src/spearmint/configuration/dynamic_value.py)

## Solution options
1. Use public `pydantic` schema APIs for custom types.
2. Drop schema support for `DynamicValue` and treat it as a plain iterable at runtime.
3. Isolate the private import behind a compatibility layer with version checks.

## Recommendation
Option 1 if feasible with Pydantic v2 public hooks. If not, option 3 to reduce breakage risk.