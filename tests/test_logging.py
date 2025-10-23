"""Tests for logging backend implementations."""

from spearmint.branch import Branch
from spearmint.logging import InMemoryLogger


class TestInMemoryLogger:
    """Test InMemoryLogger functionality."""

    def test_start_run_initializes_tracking(self):
        """start_run should initialize tracking for a new run."""
        logger = InMemoryLogger()
        logger.start_run("run-123")

        assert "run-123" in logger.runs
        assert logger.runs["run-123"]["started"] is True
        assert logger.runs["run-123"]["ended"] is False

    def test_end_run_marks_run_ended(self):
        """end_run should mark run as ended."""
        logger = InMemoryLogger()
        logger.start_run("run-123")
        logger.end_run("run-123")

        assert logger.runs["run-123"]["ended"] is True

    def test_log_params_stores_parameters(self):
        """log_params should store parameters for a run."""
        logger = InMemoryLogger()
        logger.start_run("run-123")
        logger.log_params("run-123", {"model": "gpt-4", "temperature": 0.7})

        assert logger.params["run-123"]["model"] == "gpt-4"
        assert logger.params["run-123"]["temperature"] == 0.7

    def test_log_params_updates_existing_params(self):
        """log_params should update existing parameters."""
        logger = InMemoryLogger()
        logger.start_run("run-123")
        logger.log_params("run-123", {"model": "gpt-4"})
        logger.log_params("run-123", {"temperature": 0.7})

        assert logger.params["run-123"]["model"] == "gpt-4"
        assert logger.params["run-123"]["temperature"] == 0.7

    def test_log_metrics_stores_metrics(self):
        """log_metrics should store metrics for a run."""
        logger = InMemoryLogger()
        logger.start_run("run-123")
        logger.log_metrics("run-123", {"duration": 1.5, "accuracy": 0.95})

        assert logger.metrics["run-123"]["duration"] == 1.5
        assert logger.metrics["run-123"]["accuracy"] == 0.95

    def test_log_branch_appends_branch(self):
        """log_branch should append branch to run's branch list."""
        logger = InMemoryLogger()
        logger.start_run("run-123")

        branch = Branch.start("config-1", {"model": "gpt-4"})
        branch.mark_success({"result": "success"})
        logger.log_branch("run-123", branch)

        assert len(logger.branches["run-123"]) == 1
        assert logger.branches["run-123"][0].config_id == "config-1"

    def test_log_multiple_branches(self):
        """log_branch should append multiple branches."""
        logger = InMemoryLogger()
        logger.start_run("run-123")

        for i in range(3):
            branch = Branch.start(f"config-{i}", {"x": i})
            branch.mark_success({"result": i})
            logger.log_branch("run-123", branch)

        assert len(logger.branches["run-123"]) == 3

    def test_get_run_count_returns_total_runs(self):
        """get_run_count should return total number of runs."""
        logger = InMemoryLogger()
        logger.start_run("run-1")
        logger.start_run("run-2")
        logger.start_run("run-3")

        assert logger.get_run_count() == 3

    def test_get_branch_count_all_runs(self):
        """get_branch_count without run_id should return total branches."""
        logger = InMemoryLogger()

        logger.start_run("run-1")
        logger.log_branch("run-1", Branch.start("c1", {}))
        logger.log_branch("run-1", Branch.start("c2", {}))

        logger.start_run("run-2")
        logger.log_branch("run-2", Branch.start("c3", {}))

        assert logger.get_branch_count() == 3

    def test_get_branch_count_specific_run(self):
        """get_branch_count with run_id should return branches for that run."""
        logger = InMemoryLogger()

        logger.start_run("run-1")
        logger.log_branch("run-1", Branch.start("c1", {}))
        logger.log_branch("run-1", Branch.start("c2", {}))

        logger.start_run("run-2")
        logger.log_branch("run-2", Branch.start("c3", {}))

        assert logger.get_branch_count("run-1") == 2
        assert logger.get_branch_count("run-2") == 1

    def test_get_branch_count_nonexistent_run(self):
        """get_branch_count for non-existent run should return 0."""
        logger = InMemoryLogger()
        assert logger.get_branch_count("nonexistent") == 0
