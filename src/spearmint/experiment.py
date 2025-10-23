"""Experiment decorator and orchestration.

This module provides the @experiment decorator for wrapping async functions
with multi-branch execution strategies and config pool management.

Acceptance Criteria Reference: Section 2.6 (Experiment Decorator)
- @experiment decorator wrapping async functions
- Strategy delegation and config pool injection
- Inspection hooks for accessing branch results

TODO:
- Implement @experiment decorator with strategy selection
- Add config pool management and injection
- Provide inspection API (e.g., last_branch property for single-result strategies)
- Handle both async and sync function wrapping (with sync->async conversion)
- Integrate with logging backend
- Support decorator parameters (strategy, logger, etc.)
"""
