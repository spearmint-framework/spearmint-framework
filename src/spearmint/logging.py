"""Logging backend abstraction and implementations.

This module provides a pluggable logging interface for experiment tracking,
with support for MLflow and in-memory test backends.

Acceptance Criteria Reference: Section 2.4 (Logging Layer)
- LoggerBackend protocol defining logging interface
- MLflow backend implementation with graceful fallback
- InMemoryLogger for testing

TODO:
- Define LoggerBackend protocol (log_branch, start_run, end_run methods)
- Implement MLflowBackend with guarded import (try/except ImportError)
- Implement InMemoryLogger for unit tests
- Ensure no-op behavior when MLflow not installed
- Add configuration options (experiment name, tracking URI, etc.)
"""
