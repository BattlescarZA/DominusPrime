# -*- coding: utf-8 -*-
"""
Tests for self-improvement system.
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.dominusprime.agents.self_improvement.config import (
    ImprovementConfig,
    ImprovementPolicy,
    ExperimentMetadata,
)
from src.dominusprime.agents.self_improvement.evaluator import (
    EvaluationResult,
    TestSuite,
    SkillTestSuite,
    Evaluator,
)
from src.dominusprime.agents.self_improvement.experiment import (
    Experiment,
    ExperimentLog,
)


class TestImprovementConfig:
    """Test ImprovementConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ImprovementConfig(
            metric_name="test_metric",
        )
        
        assert config.metric_name == "test_metric"
        assert config.time_budget_seconds == 300
        assert config.evaluation_samples == 20
        assert config.git_enabled is True
        assert config.improvement_threshold == 0.001
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ImprovementConfig(
            metric_name="f1_score",
            time_budget_seconds=600,
            evaluation_samples=50,
            improvement_threshold=0.01,
            max_iterations=100,
        )
        
        assert config.metric_name == "f1_score"
        assert config.time_budget_seconds == 600
        assert config.evaluation_samples == 50
        assert config.improvement_threshold == 0.01
        assert config.max_iterations == 100
    
    def test_invalid_config(self):
        """Test validation of invalid configurations."""
        with pytest.raises(ValueError):
            ImprovementConfig(
                metric_name="test",
                improvement_threshold=-0.1,  # Negative threshold
            )
        
        with pytest.raises(ValueError):
            ImprovementConfig(
                metric_name="test",
                time_budget_seconds=0,  # Zero time budget
            )


class TestImprovementPolicy:
    """Test ImprovementPolicy class."""
    
    def test_default_policy(self):
        """Test default policy settings."""
        policy = ImprovementPolicy()
        
        assert policy.alert_on_performance_drop is True
        assert policy.sandbox_experiments is True
        assert policy.kill_switch_enabled is True
    
    def test_file_allowed_with_forbidden_patterns(self):
        """Test forbidden pattern matching."""
        policy = ImprovementPolicy(
            allowed_files=[],
            forbidden_patterns=[r"password", r"secret", r"__version__"],
        )
        
        # Should be forbidden
        assert not policy.is_file_allowed("config/password.txt")
        assert not policy.is_file_allowed("src/secret_key.py")
        assert not policy.is_file_allowed("__version__.py")
        
        # Should be allowed
        assert policy.is_file_allowed("src/skill.py")
        assert policy.is_file_allowed("tests/test_skill.py")
    
    def test_file_allowed_with_allow_list(self):
        """Test explicit allow list."""
        policy = ImprovementPolicy(
            allowed_files=["src/skills/", "tests/"],
        )
        
        # Should be allowed
        assert policy.is_file_allowed("src/skills/web_search.py")
        assert policy.is_file_allowed("tests/test_skill.py")
        
        # Should be forbidden (not in allow list)
        assert not policy.is_file_allowed("src/core/agent.py")
    
    def test_requires_approval(self):
        """Test approval requirements."""
        policy = ImprovementPolicy(
            require_human_approval_for=["security", "data_access"],
        )
        
        assert policy.requires_approval("security")
        assert policy.requires_approval("data_access")
        assert not policy.requires_approval("performance")


class TestEvaluationResult:
    """Test EvaluationResult class."""
    
    def test_basic_result(self):
        """Test basic evaluation result."""
        result = EvaluationResult(
            metric_value=0.85,
            metric_name="f1_score",
            execution_time_seconds=10.5,
            memory_mb=512,
            tests_passed=8,
            tests_failed=2,
            tests_total=10,
        )
        
        assert result.metric_value == 0.85
        assert result.test_pass_rate == 0.8
        assert result.success is True
    
    def test_is_better_than(self):
        """Test comparison between results."""
        baseline = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
        )
        
        better = EvaluationResult(
            metric_value=0.85,
            metric_name="score",
        )
        
        worse = EvaluationResult(
            metric_value=0.75,
            metric_name="score",
        )
        
        assert better.is_better_than(baseline, threshold=0.01)
        assert not worse.is_better_than(baseline, threshold=0.01)
        assert not baseline.is_better_than(baseline, threshold=0.01)
    
    def test_total_score_with_simplicity(self):
        """Test total score calculation with simplicity bonus."""
        result1 = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
            lines_of_code=100,
            complexity_score=5.0,
        )
        
        result2 = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
            lines_of_code=50,
            complexity_score=2.0,
        )
        
        # Result2 should have better total score (simpler)
        assert result2.total_score > result1.total_score


class TestExperiment:
    """Test Experiment class."""
    
    def test_experiment_creation(self):
        """Test creating an experiment."""
        exp = Experiment(
            commit_hash="abc123f",
            experiment_id="exp_001",
            timestamp="2026-03-29 20:00:00",
            hypothesis="Increase learning rate",
            strategy="incremental",
            metric_value=0.85,
            metric_name="accuracy",
            memory_gb=2.5,
            execution_time=30.0,
            status="keep",
        )
        
        assert exp.commit_hash == "abc123f"
        assert exp.status == "keep"
        assert exp.metric_value == 0.85
    
    def test_to_tsv_row(self):
        """Test TSV row conversion."""
        exp = Experiment(
            commit_hash="abc123f456",
            experiment_id="exp_001",
            timestamp="2026-03-29 20:00:00",
            hypothesis="Test hypothesis",
            strategy="incremental",
            metric_value=0.997900,
            metric_name="val_bpb",
            memory_gb=44.0,
            execution_time=300.0,
            status="keep",
        )
        
        row = exp.to_tsv_row()
        
        # Check format: commit(7 chars), metric(6 decimals), memory(1 decimal), status, description
        assert row[0] == "abc123f"  # Short hash
        assert row[1] == "0.997900"
        assert row[2] == "44.0"
        assert row[3] == "keep"
        assert row[4] == "Test hypothesis"


class TestExperimentLog:
    """Test ExperimentLog class."""
    
    def test_log_initialization(self):
        """Test log file initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = ExperimentLog(tmpdir, "test_experiment")
            
            # Check files are created
            assert log.tsv_path.exists()
            assert log.json_path.exists()
            
            # Check TSV header
            with open(log.tsv_path, 'r') as f:
                header = f.readline().strip()
                assert header == "commit\tval_metric\tmemory_gb\tstatus\tdescription"
    
    def test_log_experiment(self):
        """Test logging an experiment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = ExperimentLog(tmpdir, "test_experiment")
            
            exp = Experiment(
                commit_hash="abc123f",
                experiment_id="exp_001",
                timestamp="2026-03-29 20:00:00",
                hypothesis="Test",
                strategy="incremental",
                metric_value=0.85,
                metric_name="score",
                memory_gb=2.0,
                execution_time=10.0,
                status="keep",
            )
            
            log.log_experiment(exp)
            
            # Check it's in memory
            assert len(log.experiments) == 1
            assert log.experiments[0].commit_hash == "abc123f"
            
            # Check it's in TSV file
            with open(log.tsv_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2  # Header + 1 experiment
            
            # Check it's in JSON file
            with open(log.json_path, 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]['commit_hash'] == "abc123f"
    
    def test_get_baseline(self):
        """Test retrieving baseline experiment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = ExperimentLog(tmpdir, "test_experiment")
            
            # Log baseline
            baseline = Experiment(
                commit_hash="baseline",
                experiment_id="exp_000",
                timestamp="2026-03-29 20:00:00",
                hypothesis="baseline",
                strategy="baseline",
                metric_value=0.80,
                metric_name="score",
                memory_gb=2.0,
                execution_time=10.0,
                status="keep",
            )
            log.log_experiment(baseline)
            
            # Log another experiment
            exp2 = Experiment(
                commit_hash="abc123f",
                experiment_id="exp_001",
                timestamp="2026-03-29 20:01:00",
                hypothesis="improvement",
                strategy="incremental",
                metric_value=0.85,
                metric_name="score",
                memory_gb=2.0,
                execution_time=10.0,
                status="keep",
            )
            log.log_experiment(exp2)
            
            # Baseline should be the first kept experiment
            retrieved = log.get_baseline()
            assert retrieved is not None
            assert retrieved.commit_hash == "baseline"
    
    def test_get_best(self):
        """Test retrieving best experiment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = ExperimentLog(tmpdir, "test_experiment")
            
            # Log multiple experiments
            for i, (value, status) in enumerate([
                (0.80, "keep"),
                (0.85, "keep"),
                (0.75, "discard"),
                (0.90, "keep"),
            ]):
                exp = Experiment(
                    commit_hash=f"commit_{i}",
                    experiment_id=f"exp_{i:03d}",
                    timestamp="2026-03-29 20:00:00",
                    hypothesis=f"exp {i}",
                    strategy="incremental",
                    metric_value=value,
                    metric_name="score",
                    memory_gb=2.0,
                    execution_time=10.0,
                    status=status,
                )
                log.log_experiment(exp)
            
            # Best should be the highest metric among kept experiments
            best = log.get_best()
            assert best is not None
            assert best.metric_value == 0.90
            assert best.commit_hash == "commit_3"


class TestEvaluator:
    """Test Evaluator class."""
    
    def test_compare_results_keep(self):
        """Test comparison that results in keep."""
        baseline = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
        )
        
        improved = EvaluationResult(
            metric_value=0.85,
            metric_name="score",
        )
        
        suite = SkillTestSuite("test")
        evaluator = Evaluator(suite)
        
        decision = evaluator.compare_results(improved, baseline, threshold=0.01)
        assert decision == "keep"
    
    def test_compare_results_discard(self):
        """Test comparison that results in discard."""
        baseline = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
        )
        
        worse = EvaluationResult(
            metric_value=0.75,
            metric_name="score",
        )
        
        suite = SkillTestSuite("test")
        evaluator = Evaluator(suite)
        
        decision = evaluator.compare_results(worse, baseline, threshold=0.01)
        assert decision == "discard"
    
    def test_compare_results_crash(self):
        """Test comparison with crashed experiment."""
        baseline = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
        )
        
        crashed = EvaluationResult(
            metric_value=0.0,
            metric_name="score",
            success=False,
            error_message="Out of memory",
        )
        
        suite = SkillTestSuite("test")
        evaluator = Evaluator(suite)
        
        decision = evaluator.compare_results(crashed, baseline, threshold=0.01)
        assert decision == "crash"
    
    def test_compare_results_simplicity_wins(self):
        """Test that simpler code wins with equal performance."""
        baseline = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
            lines_of_code=200,
        )
        
        simpler = EvaluationResult(
            metric_value=0.80,
            metric_name="score",
            lines_of_code=100,
        )
        
        suite = SkillTestSuite("test")
        evaluator = Evaluator(suite)
        
        decision = evaluator.compare_results(simpler, baseline, threshold=0.01)
        assert decision == "keep"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
