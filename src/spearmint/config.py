"""Configuration management utilities.

This module provides utilities for loading, expanding, and managing experiment
configurations from YAML files and Pydantic models.

Acceptance Criteria Reference: Section 2.5 (Configuration Management)
- YAML loader for directory and file paths
- Pydantic expansion for model-driven variant generation
- Config ID canonicalization and hashing

TODO:
- Implement YAML loader (load_configs_from_yaml) supporting files and directories
- Add Pydantic expansion utility (expand_configs_from_model)
- Implement config_id generation (hash-based canonicalization)
- Add validation and error handling for malformed configs
- Support both dict and BaseModel config types
"""
