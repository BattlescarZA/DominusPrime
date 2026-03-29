# -*- coding: utf-8 -*-
"""
Evaluation system for measuring improvement.
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod


@dataclass
class EvaluationResult:
    """Result of an evaluation run."""
    
    # Primary metric
    metric_value: float
    metric_name: str
    
    # Secondary metrics
    secondary_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Performance data
    execution_time_seconds: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    
    # Test results
    tests_passed: int = 0
    tests_failed: int = 0
    tests_total: int = 0
    
    # Code metrics
    lines_of_code: int = 0
    complexity_score: float = 0.0
    
    # Status
    success: bool = True
    error_message: Optional[str] = None
    
    # Metadata
    timestamp: str = ""
    
    @property
    def test_pass_rate(self) -> float:
        """Calculate test pass rate."""
        if self.tests_total == 0:
            return 0.0
        return self.tests_passed / self.tests_total
    
    @property
    def total_score(self) -> float:
        """
        Calculate total score combining primary metric and other factors.
        Higher is better (assumes metric is already normalized this way).
        """
        base_score = self.metric_value
        
        # Bonus for simplicity (fewer lines = better)
        if self.lines_of_code > 0:
            simplicity_bonus = -self.complexity_score * 0.01
            base_score += simplicity_bonus
        
        # Penalty for failed tests
        if self.tests_total > 0:
            test_penalty = (1.0 - self.test_pass_rate) * 0.1
            base_score -= test_penalty
        
        return base_score
    
    def is_better_than(self, other: "EvaluationResult", threshold: float = 0.001) -> bool:
        """
        Check if this result is better than another.
        
        Args:
            other: Other evaluation result to compare against
            threshold: Minimum improvement to consider "better"
        
        Returns:
            True if this result is meaningfully better
        """
        improvement = self.total_score - other.total_score
        return improvement > threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_value": self.metric_value,
            "metric_name": self.metric_name,
            "secondary_metrics": self.secondary_metrics,
            "execution_time": self.execution_time_seconds,
            "memory_mb": self.memory_mb,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "test_pass_rate": self.test_pass_rate,
            "lines_of_code": self.lines_of_code,
            "complexity_score": self.complexity_score,
            "total_score": self.total_score,
            "success": self.success,
            "error_message": self.error_message,
        }


class TestSuite(ABC):
    """Abstract base class for test suites."""
    
    def __init__(self, name: str):
        self.name = name
        self.test_cases: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def run_evaluation(self, target: Any) -> EvaluationResult:
        """
        Run the test suite against a target (skill, agent, etc.).
        
        Args:
            target: The object to evaluate
        
        Returns:
            Evaluation result with metrics
        """
        pass
    
    def add_test_case(self, test_case: Dict[str, Any]):
        """Add a test case to the suite."""
        self.test_cases.append(test_case)
    
    def load_test_cases(self, filepath: str):
        """Load test cases from a file."""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            self.test_cases.extend(cases)


class SkillTestSuite(TestSuite):
    """Test suite for evaluating skills."""
    
    async def run_evaluation(self, skill: Any) -> EvaluationResult:
        """
        Evaluate a skill against test cases.
        
        Args:
            skill: The skill to evaluate
        
        Returns:
            Evaluation result
        """
        start_time = time.time()
        passed = 0
        failed = 0
        total = len(self.test_cases)
        
        metric_scores = []
        
        for test_case in self.test_cases:
            try:
                # Run the skill
                result = await skill.execute(**test_case.get("input", {}))
                
                # Evaluate result
                expected = test_case.get("expected")
                score = self._score_result(result, expected)
                metric_scores.append(score)
                
                if score >= 0.7:  # 70% threshold for pass
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                print(f"Test case failed with error: {e}")
        
        execution_time = time.time() - start_time
        
        # Calculate primary metric (average score)
        avg_score = sum(metric_scores) / len(metric_scores) if metric_scores else 0.0
        
        return EvaluationResult(
            metric_value=avg_score,
            metric_name="average_score",
            execution_time_seconds=execution_time,
            tests_passed=passed,
            tests_failed=failed,
            tests_total=total,
            success=True,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
    
    def _score_result(self, result: Any, expected: Any) -> float:
        """
        Score a result against expected output.
        Override this for custom scoring logic.
        
        Returns:
            Score from 0.0 to 1.0
        """
        # Simple exact match
        if result == expected:
            return 1.0
        return 0.0


class AgentTestSuite(TestSuite):
    """Test suite for evaluating agents."""
    
    async def run_evaluation(self, agent: Any) -> EvaluationResult:
        """
        Evaluate an agent through interaction scenarios.
        
        Args:
            agent: The agent to evaluate
        
        Returns:
            Evaluation result
        """
        start_time = time.time()
        passed = 0
        failed = 0
        total = len(self.test_cases)
        
        scenario_scores = []
        
        for scenario in self.test_cases:
            try:
                # Run scenario
                score = await self._run_scenario(agent, scenario)
                scenario_scores.append(score)
                
                if score >= 0.7:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                print(f"Scenario failed with error: {e}")
        
        execution_time = time.time() - start_time
        avg_score = sum(scenario_scores) / len(scenario_scores) if scenario_scores else 0.0
        
        return EvaluationResult(
            metric_value=avg_score,
            metric_name="scenario_success_rate",
            execution_time_seconds=execution_time,
            tests_passed=passed,
            tests_failed=failed,
            tests_total=total,
            success=True,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
    
    async def _run_scenario(self, agent: Any, scenario: Dict[str, Any]) -> float:
        """
        Run a single scenario and return score.
        
        Returns:
            Score from 0.0 to 1.0
        """
        # This would be implemented based on scenario type
        # For now, return a placeholder
        return 0.8


class Evaluator:
    """Main evaluator for running experiments."""
    
    def __init__(self, test_suite: TestSuite):
        self.test_suite = test_suite
    
    async def evaluate(
        self, 
        target: Any,
        time_budget_seconds: Optional[int] = None
    ) -> EvaluationResult:
        """
        Evaluate a target with optional time budget.
        
        Args:
            target: Object to evaluate
            time_budget_seconds: Maximum time allowed for evaluation
        
        Returns:
            Evaluation result
        """
        if time_budget_seconds:
            try:
                result = await asyncio.wait_for(
                    self.test_suite.run_evaluation(target),
                    timeout=time_budget_seconds
                )
                return result
            except asyncio.TimeoutError:
                return EvaluationResult(
                    metric_value=0.0,
                    metric_name=self.test_suite.name,
                    success=False,
                    error_message=f"Evaluation exceeded time budget ({time_budget_seconds}s)",
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                )
        else:
            return await self.test_suite.run_evaluation(target)
    
    def compare_results(
        self,
        new_result: EvaluationResult,
        baseline: EvaluationResult,
        threshold: float = 0.001
    ) -> str:
        """
        Compare two results and return decision.
        
        Args:
            new_result: New experiment result
            baseline: Baseline to compare against
            threshold: Improvement threshold
        
        Returns:
            Decision: "keep", "discard", or "crash"
        """
        if not new_result.success:
            return "crash"
        
        if new_result.is_better_than(baseline, threshold):
            return "keep"
        
        # Check if it's equal (within threshold)
        diff = abs(new_result.total_score - baseline.total_score)
        if diff <= threshold / 2:  # Within half the threshold
            # Equal performance - prefer simpler code
            if new_result.lines_of_code < baseline.lines_of_code:
                return "keep"
        
        return "discard"
