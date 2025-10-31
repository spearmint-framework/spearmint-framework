"""Tests for Branch and BranchContainer data models."""

import time

import pytest

from spearmint.branch import Branch, BranchContainer


class TestBranch:
    """Test Branch dataclass and lifecycle methods."""

    def test_branch_start_initializes_correctly(self):
        """Branch.start should create branch with correct defaults."""
        config = {"model": "gpt-4", "temperature": 0.7}
        branch = Branch.start("config-123", config)

        assert branch.config_id == "config-123"
        assert branch.config == config
        assert branch.start_ts > 0
        assert branch.end_ts is None
        assert branch.status == "pending"
        assert branch.output is None
        assert branch.exception_info is None

    def test_mark_success_sets_correct_fields(self):
        """mark_success should set status, end_ts, and output."""
        branch = Branch.start("config-123", {"model": "gpt-4"})
        time.sleep(0.01)  # Ensure measurable duration

        output = {"result": "success"}
        branch.mark_success(output)

        assert branch.status == "success"
        assert branch.end_ts is not None
        assert branch.end_ts > branch.start_ts
        assert branch.output == output
        assert branch.exception_info is None

    def test_mark_failure_captures_exception_info(self):
        """mark_failure should set status and capture exception details."""
        branch = Branch.start("config-123", {"model": "gpt-4"})

        try:
            raise ValueError("Test error message")
        except ValueError as e:
            branch.mark_failure(e)

        assert branch.status == "failed"
        assert branch.end_ts is not None
        assert branch.output is None
        assert branch.exception_info is not None
        assert branch.exception_info["type"] == "ValueError"
        assert branch.exception_info["message"] == "Test error message"
        assert "ValueError" in branch.exception_info["traceback"]
        assert "test_mark_failure_captures_exception_info" in branch.exception_info["traceback"]

    def test_mark_skipped_sets_status(self):
        """mark_skipped should set status and store reason."""
        branch = Branch.start("config-123", {"model": "gpt-4"})

        branch.mark_skipped("Rate limit exceeded")

        assert branch.status == "skipped"
        assert branch.end_ts is not None
        assert branch.exception_info is not None
        assert branch.exception_info["type"] == "Skipped"
        assert branch.exception_info["message"] == "Rate limit exceeded"

    def test_duration_returns_none_before_completion(self):
        """duration should return None if branch not completed."""
        branch = Branch.start("config-123", {"model": "gpt-4"})

        assert branch.duration is None

    def test_duration_returns_positive_value_after_completion(self):
        """duration should return positive value after completion."""
        branch = Branch.start("config-123", {"model": "gpt-4"})
        time.sleep(0.01)
        branch.mark_success({"result": "done"})

        assert branch.duration is not None
        assert branch.duration >= 0

    def test_mark_success_twice_raises_error(self):
        """Marking success twice should raise RuntimeError."""
        branch = Branch.start("config-123", {"model": "gpt-4"})
        branch.mark_success({"result": "done"})

        with pytest.raises(RuntimeError, match="already finalized"):
            branch.mark_success({"result": "again"})

    def test_mark_failure_after_success_raises_error(self):
        """Marking failure after success should raise RuntimeError."""
        branch = Branch.start("config-123", {"model": "gpt-4"})
        branch.mark_success({"result": "done"})

        with pytest.raises(RuntimeError, match="already finalized"):
            branch.mark_failure(Exception("late error"))

    def test_exception_with_unicode_message_serialized_correctly(self):
        """Exception with Unicode characters should serialize correctly."""
        branch = Branch.start("config-123", {"model": "gpt-4"})

        try:
            raise ValueError("Error with emoji 🚀 and unicode ñ")
        except ValueError as e:
            branch.mark_failure(e)

        assert "🚀" in branch.exception_info["message"]
        assert "ñ" in branch.exception_info["message"]

    def test_to_dict_includes_expected_keys(self):
        """to_dict should include all expected keys."""
        branch = Branch.start("config-123", {"model": "gpt-4"})
        branch.mark_success({"result": "done"})

        d = branch.to_dict()

        assert "config_id" in d
        assert "config" in d
        assert "start_ts" in d
        assert "end_ts" in d
        assert "status" in d
        assert "output" in d
        assert "exception_info" in d
        assert "duration" in d
        assert d["config_id"] == "config-123"
        assert d["status"] == "success"


class TestBranchContainer:
    """Test BranchContainer collection management."""

    def test_container_iteration(self):
        """BranchContainer should support iteration."""
        b1 = Branch.start("c1", {"x": 1})
        b2 = Branch.start("c2", {"x": 2})
        b1.mark_success({"r": 1})
        b2.mark_success({"r": 2})

        container = BranchContainer([b1, b2])

        branches = list(container)
        assert len(branches) == 2
        assert branches[0].config_id == "c1"
        assert branches[1].config_id == "c2"

    def test_container_len(self):
        """BranchContainer should support len()."""
        b1 = Branch.start("c1", {"x": 1})
        container = BranchContainer([b1])

        assert len(container) == 1

    def test_container_getitem(self):
        """BranchContainer should support indexing."""
        b1 = Branch.start("c1", {"x": 1})
        b2 = Branch.start("c2", {"x": 2})
        container = BranchContainer([b1, b2])

        assert container[0].config_id == "c1"
        assert container[1].config_id == "c2"

    def test_successful_returns_only_success_branches(self):
        """successful() should filter only successful branches."""
        b1 = Branch.start("c1", {"x": 1})
        b2 = Branch.start("c2", {"x": 2})
        b3 = Branch.start("c3", {"x": 3})

        b1.mark_success({"r": 1})
        b2.mark_failure(Exception("error"))
        b3.mark_success({"r": 3})

        container = BranchContainer([b1, b2, b3])
        successful = container.successful()

        assert len(successful) == 2
        assert all(b.status == "success" for b in successful)
        assert {b.config_id for b in successful} == {"c1", "c3"}

    def test_failed_returns_only_failed_branches(self):
        """failed() should filter only failed branches."""
        b1 = Branch.start("c1", {"x": 1})
        b2 = Branch.start("c2", {"x": 2})
        b3 = Branch.start("c3", {"x": 3})

        b1.mark_success({"r": 1})
        b2.mark_failure(Exception("error"))
        b3.mark_failure(Exception("error2"))

        container = BranchContainer([b1, b2, b3])
        failed = container.failed()

        assert len(failed) == 2
        assert all(b.status == "failed" for b in failed)
        assert {b.config_id for b in failed} == {"c2", "c3"}

    def test_by_config_id_returns_correct_branch(self):
        """by_config_id should return branch with matching config_id."""
        b1 = Branch.start("c1", {"x": 1})
        b2 = Branch.start("c2", {"x": 2})
        b3 = Branch.start("c3", {"x": 3})

        container = BranchContainer([b1, b2, b3])

        found = container.by_config_id("c2")
        assert found is not None
        assert found.config_id == "c2"
        assert found.config == {"x": 2}

    def test_by_config_id_returns_none_if_not_found(self):
        """by_config_id should return None if no match found."""
        b1 = Branch.start("c1", {"x": 1})
        container = BranchContainer([b1])

        found = container.by_config_id("nonexistent")
        assert found is None
