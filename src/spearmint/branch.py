"""Branch data structures for experiment execution tracking.

This module provides core data models for tracking individual experiment branches,
including configuration, timing, status, and results.

Acceptance Criteria Reference: Section 2.2 (Branch Model)
- Branch dataclass with config_id, config, timestamps, status, output, exception info
- Factory methods for lifecycle management (start, mark_success, mark_failure)
- BranchContainer for managing collections of branches

TODO:
- Implement Branch dataclass with all required fields
- Add ExceptionInfo structure for error capture
- Implement BranchContainer with filtering methods
- Add serialization helpers (to_dict with optional redaction)
"""
