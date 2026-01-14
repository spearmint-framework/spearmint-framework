"""Result formatter for experiment branch outputs.

This module provides utilities for traversing the BranchScope tree
and formatting results into a structured output format.
"""

from typing import Any

from .context import BranchScope


def format_branch_results(root_scope: BranchScope) -> list[dict[str, Any]]:
    """Format all branch results from a scope tree into structured output.

    Traverses the scope tree and collects all unique execution paths,
    building a config_chain and outputs dictionary for each path.

    Args:
        root_scope: The root BranchScope from which to collect results.

    Returns:
        A list of result records, each containing:
        - config_chain: List of config_ids in the execution path
        - outputs: Dict mapping config_id to {output, default} records

    Example output:
        [
            {
                "config_chain": ["config1", "configA"],
                "outputs": {
                    "config1": {"output": "...", "default": True},
                    "configA": {"output": "...", "default": True},
                }
            },
            ...
        ]
    """
    paths: list[dict[str, Any]] = []
    _collect_paths(root_scope, [], {}, paths)
    return paths


def _collect_paths(
    scope: BranchScope,
    current_chain: list[str],
    current_outputs: dict[str, dict[str, Any]],
    paths: list[dict[str, Any]],
) -> None:
    """Recursively collect execution paths from the scope tree.

    Args:
        scope: Current scope being processed.
        current_chain: Config IDs accumulated so far in this path.
        current_outputs: Outputs accumulated so far in this path.
        paths: List to append completed paths to.
    """
    # Check if this scope has branch data
    branch = scope.branch
    config_id = None
    
    if branch is not None:
        config_id = branch.config_id
        # Add this branch's contribution to the path
        current_chain = current_chain + [config_id]
        current_outputs = {
            **current_outputs,
            config_id: {
                "output": branch.output,
                "default": branch.default,
            },
        }
    elif "output" in scope.data and scope.data.get("func"):
        # This is a function call scope without a branch (e.g., non-decorated function)
        # We still want to track its output if it exists
        pass

    if not scope.children:
        # Leaf node - this is a complete path
        if current_chain:  # Only add if we have at least one config
            paths.append({
                "config_chain": current_chain,
                "outputs": current_outputs,
            })
    else:
        # Recurse into children
        for child in scope.children:
            _collect_paths(child, current_chain, current_outputs, paths)


def get_default_output(root_scope: BranchScope) -> Any:
    """Get the output from the default branch path.

    Traverses the scope tree following only default branches
    and returns the final output.

    Args:
        root_scope: The root BranchScope to start from.

    Returns:
        The output from the default branch, or None if not found.
    """
    return _find_default_output(root_scope)


def _find_default_output(scope: BranchScope) -> Any:
    """Recursively find the default branch output.

    Args:
        scope: Current scope being searched.

    Returns:
        The default output, or None if not found.
    """
    # If this scope has a branch that is default, check its output
    if scope.branch is not None and scope.branch.default:
        if not scope.children:
            return scope.branch.output
        # Continue searching in children for deeper default
        for child in scope.children:
            result = _find_default_output(child)
            if result is not None:
                return result
        # If no deeper default found, return this branch's output
        return scope.branch.output

    # Search children for default
    for child in scope.children:
        result = _find_default_output(child)
        if result is not None:
            return result

    # Check if this scope has direct output (non-branched function)
    if "output" in scope.data:
        return scope.data["output"]

    return None
