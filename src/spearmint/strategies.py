"""Strategy implementations for experiment execution patterns.

This module defines the Strategy protocol and provides built-in implementations:
- RoundRobinStrategy: Cycles through configs sequentially
- ShadowStrategy: Runs primary + shadows concurrently
- MultiBranchStrategy: Runs all configs concurrently

Acceptance Criteria Reference: Section 2.3 (Strategy Protocol & Built-ins)
- Strategy protocol defining execute interface
- Built-in strategies with proper concurrency semantics
- Consistent branch creation and logging per strategy

TODO:
- Define Strategy Protocol with execute() method signature
- Implement RoundRobinStrategy
- Implement ShadowStrategy with primary/shadow distinction
- Implement MultiBranchStrategy with concurrent execution
- Ensure proper asyncio task management for background vs awaited tasks
"""
