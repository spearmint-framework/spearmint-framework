# Spearmint MVP Implementation Task Plan

Guiding principles: DRY, YAGNI, TDD-first (write/extend tests before production code), frequent small commits (each task or subtask), clear separation of concerns, minimal surface area for MVP.

## High-Level Task Outline

1. Project & Dependency Baseline
   - Confirm `pyproject.toml` structure, add optional MLflow dependency (extras) and Pydantic.
   - Add dev tooling: pytest, mypy, ruff (or flake8), coverage config.

2. Core Types & Data Models
   - Implement `Branch` dataclass and related `BranchContainer` abstraction.
   - Define common enums / constants (status strings) and type aliases in `types.py`.

3. Logging Layer
   - Define `LoggerBackend` protocol.
   - Implement MLflow backend (guarded import, graceful no-MLflow fallback).
   - Add minimal test double (InMemoryLogger) for unit tests.

4. Strategy Protocol & Built-in Strategies
   - Define `Strategy` protocol interface.
   - Implement `RoundRobinStrategy`, `ShadowStrategy`, `MultiBranchStrategy` with concurrency semantics.
   - Ensure consistent branch creation & logging per strategy.

## Detailed Task 1

See separate plan: [Task 1: Project & Dependency Baseline](./task-1-project-dependency-baseline.md)

## Detailed Task 2

See separate plan: [Task 2: Core Types & Data Models](./task-2-core-types-data-models.md)


## Detailed Task 3

See separate plan: [Task 3: Logging Layer](./task-3-logging-layer.md)

## Detailed Task 4

See separate plan: [Task 4: Strategy Protocol & Built-in Strategies](./task-4-strategy-protocol-builtins.md)


