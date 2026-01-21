# Make parse_configs strict and explicit

## Overview
`parse_configs` accepts `Any` and silently ignores unsupported values. That makes failures hard to debug and hides configuration mistakes.

## Relevant code
- [src/spearmint/configuration/__init__.py](src/spearmint/configuration/__init__.py)

## Solution options
1. Raise a `TypeError` for unsupported inputs with a clear message.
2. Add a `strict` flag defaulting to true, with a warning in non-strict mode.
3. Validate input types earlier in the public API and keep parse_configs internal.

## Recommendation
Option 1. Clear errors early beats hidden behavior, and it simplifies debugging.