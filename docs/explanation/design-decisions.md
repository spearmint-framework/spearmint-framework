# Design Decisions

Why Spearmint was designed the way it is.

## Decorator Pattern

**Decision:** Use decorators for experiment definition

**Rationale:**
- Minimal code changes to existing functions
- Clear visual indicator of experimental code
- Familiar Python pattern
- Easy to add/remove

**Alternative considered:** Context managers only
- Would require wrapping all calls
- More boilerplate

## Context Variables

**Decision:** Use `contextvars` for runtime state

**Rationale:**
- Thread-safe execution
- Async-safe across await boundaries
- No global mutable state
- Clean isolation between experiments

**Alternative considered:** Thread-local storage
- Not async-safe
- More complex with asyncio

## Strategy Pattern

**Decision:** Functions for strategy selection

**Rationale:**
- Simple, flexible interface
- Easy to customize
- No inheritance required
- Functional programming friendly

**Alternative considered:** Strategy classes
- More boilerplate
- Less flexible

## Type Safety

**Decision:** Pydantic for config validation

**Rationale:**
- Industry standard
- Excellent IDE support
- Runtime validation
- Clear error messages

## See Also

- [Architecture](architecture.md)
- [Comparison to Alternatives](comparison-to-alternatives.md)
