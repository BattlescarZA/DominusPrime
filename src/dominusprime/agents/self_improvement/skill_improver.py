# -*- coding: utf-8 -*-
"""
Skill-level self-improvement system.
Enables autonomous improvement of individual skills.
"""

import os
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .config import ImprovementConfig, ImprovementPolicy
from .evaluator import Evaluator, EvaluationResult, SkillTestSuite
from .experiment import Experiment, ExperimentLog, GitManager

logger = logging.getLogger(__name__)


class SkillSelfImprover:
    """
    Autonomous self-improvement for individual skills.
    
    Similar to autoresearch but for skill code optimization.
    The agent modifies skill code, runs tests, evaluates results,
    and keeps or discards changes based on objective metrics.
    """
    
    def __init__(
        self,
        skill_name: str,
        skill_path: str,
        test_suite: SkillTestSuite,
        config: ImprovementConfig,
        policy: Optional[ImprovementPolicy] = None,
    ):
        self.skill_name = skill_name
        self.skill_path = Path(skill_path)
        self.test_suite = test_suite
        self.config = config
        self.policy = policy or ImprovementPolicy()
        
        # Experiment management
        self.experiment_id = f"{skill_name}_{int(time.time())}"
        self.branch_name = f"{config.experiment_branch_prefix}/{skill_name}/{int(time.time())}"
        
        # Setup logging
        log_dir = Path(f"experiments/{self.experiment_id}")
        self.experiment_log = ExperimentLog(str(log_dir), self.experiment_id)
        
        # Git management
        if config.git_enabled:
            self.git = GitManager(os.getcwd())
        else:
            self.git = None
        
        # Evaluator
        self.evaluator = Evaluator(test_suite)
        
        # State
        self.baseline: Optional[EvaluationResult] = None
        self.current_best: Optional[EvaluationResult] = None
        self.iteration = 0
        self.consecutive_crashes = 0
        
        logger.info(f"Initialized SkillSelfImprover for {skill_name}")
    
    async def initialize_experiment(self) -> bool:
        """
        Initialize the experiment:
        1. Create git branch
        2. Verify files exist
        3. Check policy allows modification
        """
        logger.info(f"Initializing experiment for {self.skill_name}")
        
        # Check if skill file exists
        if not self.skill_path.exists():
            logger.error(f"Skill file not found: {self.skill_path}")
            return False
        
        # Check policy
        if not self.policy.is_file_allowed(str(self.skill_path)):
            logger.error(f"Policy does not allow modifying: {self.skill_path}")
            return False
        
        # Create git branch
        if self.git and self.config.git_enabled:
            if not self.git.create_branch(self.branch_name):
                logger.warning("Could not create git branch, continuing without git")
                self.git = None
        
        logger.info("Experiment initialized successfully")
        return True
    
    async def establish_baseline(self) -> EvaluationResult:
        """
        Run baseline evaluation before any modifications.
        This is the "experiment 0" that we compare all future experiments against.
        """
        logger.info("Establishing baseline...")
        
        # Load the skill
        skill = await self._load_skill()
        
        # Evaluate
        result = await self.evaluator.evaluate(
            skill,
            time_budget_seconds=self.config.time_budget_seconds
        )
        
        self.baseline = result
        self.current_best = result
        
        # Log baseline
        commit_hash = self.git.get_current_commit() if self.git else "baseline"
        experiment = Experiment(
            commit_hash=commit_hash,
            experiment_id=f"{self.experiment_id}_0",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            hypothesis="baseline",
            strategy="baseline",
            metric_value=result.metric_value,
            metric_name=result.metric_name,
            memory_gb=result.memory_mb / 1024,
            execution_time=result.execution_time_seconds,
            status="keep",
            secondary_metrics=result.secondary_metrics,
            tests_passed=result.tests_passed,
            tests_total=result.tests_total,
            lines_of_code=result.lines_of_code,
            notes="Initial baseline measurement",
        )
        self.experiment_log.log_experiment(experiment)
        
        logger.info(f"Baseline established: {result.metric_name}={result.metric_value:.6f}")
        return result
    
    async def run_improvement_loop(self, max_iterations: Optional[int] = None):
        """
        Main improvement loop - runs until manually stopped or max_iterations reached.
        
        This is the core autonomous loop inspired by autoresearch:
        1. Generate hypothesis
        2. Modify code
        3. Commit
        4. Evaluate
        5. Keep or discard
        6. Repeat
        
        Args:
            max_iterations: Maximum number of iterations (None = infinite)
        """
        # Initialize
        if not await self.initialize_experiment():
            logger.error("Failed to initialize experiment")
            return
        
        # Establish baseline
        await self.establish_baseline()
        
        # Determine iteration limit
        iterations = max_iterations or self.config.max_iterations
        
        logger.info("Starting improvement loop...")
        logger.info(f"Iterations: {'infinite' if iterations is None else iterations}")
        
        # Main loop
        while iterations is None or self.iteration < iterations:
            self.iteration += 1
            
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration {self.iteration}")
                logger.info(f"{'='*60}")
                
                # Generate hypothesis
                hypothesis = await self.generate_hypothesis()
                logger.info(f"Hypothesis: {hypothesis['description']}")
                
                # Apply modification
                previous_code = await self._read_skill_code()
                await self.apply_modification(hypothesis)
                
                # Commit if git enabled
                commit_hash = None
                if self.git and self.config.auto_commit:
                    commit_hash = self.git.commit(f"Experiment {self.iteration}: {hypothesis['description']}")
                    if not commit_hash:
                        logger.warning("Git commit failed, continuing without commit")
                        commit_hash = f"iter_{self.iteration}"
                else:
                    commit_hash = f"iter_{self.iteration}"
                
                # Evaluate
                result = await self.run_evaluation()
                
                # Decide: keep or discard
                decision = self.make_decision(result)
                logger.info(f"Decision: {decision}")
                
                # Log experiment
                await self.log_experiment(commit_hash, result, decision, hypothesis)
                
                # Handle decision
                if decision == "keep":
                    self.current_best = result
                    self.consecutive_crashes = 0
                    logger.info(f"✓ Improvement kept! New best: {result.metric_value:.6f}")
                elif decision == "crash":
                    self.consecutive_crashes += 1
                    logger.warning(f"✗ Experiment crashed ({self.consecutive_crashes}/{self.config.crash_tolerance})")
                    
                    # Revert
                    if self.git:
                        # Get previous commit (baseline or last kept)
                        best_exp = self.experiment_log.get_best()
                        if best_exp:
                            self.git.reset_to_commit(best_exp.commit_hash)
                    else:
                        # Restore previous code
                        await self._write_skill_code(previous_code)
                    
                    # Check crash tolerance
                    if self.consecutive_crashes >= self.config.crash_tolerance:
                        logger.error("Too many consecutive crashes, stopping")
                        break
                else:  # discard
                    self.consecutive_crashes = 0
                    logger.info(f"✗ Change discarded: {result.metric_value:.6f}")
                    
                    # Revert
                    if self.git:
                        best_exp = self.experiment_log.get_best()
                        if best_exp:
                            self.git.reset_to_commit(best_exp.commit_hash)
                    else:
                        await self._write_skill_code(previous_code)
                
                # Brief pause to avoid overwhelming the system
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user, stopping")
                break
            except Exception as e:
                logger.error(f"Error in improvement loop: {e}", exc_info=True)
                self.consecutive_crashes += 1
                if self.consecutive_crashes >= self.config.crash_tolerance:
                    logger.error("Too many errors, stopping")
                    break
        
        logger.info("\n" + "="*60)
        logger.info("Improvement loop completed")
        logger.info(f"Total iterations: {self.iteration}")
        
        # Print summary
        await self.print_summary()
    
    async def generate_hypothesis(self) -> Dict[str, Any]:
        """
        Generate an experimental hypothesis based on previous results.
        
        This is where the AI agent would analyze the code and experiment history
        to propose a modification. For now, returns a placeholder.
        
        Returns:
            Dictionary with hypothesis details
        """
        # In a full implementation, this would:
        # 1. Read current code
        # 2. Review experiment history
        # 3. Use LLM to generate hypothesis
        # 4. Return structured modification plan
        
        # Placeholder: cycle through strategies
        strategies = self.config.hypothesis_strategies
        strategy = strategies[self.iteration % len(strategies)]
        
        return {
            "description": f"Iteration {self.iteration} - {strategy} modification",
            "strategy": strategy,
            "modifications": [],  # Would contain specific code changes
            "expected_improvement": 0.01,  # Expected metric improvement
        }
    
    async def apply_modification(self, hypothesis: Dict[str, Any]):
        """
        Apply the hypothesized modification to the skill code.
        
        In a full implementation, this would use an LLM to modify the code
        based on the hypothesis.
        
        Args:
            hypothesis: Hypothesis dictionary with modification details
        """
        # Placeholder: actual implementation would modify the skill code
        logger.info("Applying modification (placeholder)")
        pass
    
    async def run_evaluation(self) -> EvaluationResult:
        """
        Run evaluation on the current skill version.
        
        Returns:
            Evaluation result
        """
        skill = await self._load_skill()
        result = await self.evaluator.evaluate(
            skill,
            time_budget_seconds=self.config.time_budget_seconds
        )
        return result
    
    def make_decision(self, result: EvaluationResult) -> str:
        """
        Decide whether to keep, discard, or mark as crash.
        
        Args:
            result: Evaluation result
        
        Returns:
            Decision: "keep", "discard", or "crash"
        """
        return self.evaluator.compare_results(
            result,
            self.current_best,
            threshold=self.config.improvement_threshold
        )
    
    async def log_experiment(
        self,
        commit_hash: str,
        result: EvaluationResult,
        decision: str,
        hypothesis: Dict[str, Any]
    ):
        """
        Log experiment to the experiment log.
        
        Args:
            commit_hash: Git commit hash
            result: Evaluation result
            decision: Decision made
            hypothesis: Hypothesis tested
        """
        experiment = Experiment(
            commit_hash=commit_hash,
            experiment_id=f"{self.experiment_id}_{self.iteration}",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            hypothesis=hypothesis["description"],
            strategy=hypothesis["strategy"],
            metric_value=result.metric_value if result.success else 0.0,
            metric_name=result.metric_name,
            memory_gb=result.memory_mb / 1024,
            execution_time=result.execution_time_seconds,
            status=decision,
            secondary_metrics=result.secondary_metrics,
            tests_passed=result.tests_passed,
            tests_total=result.tests_total,
            lines_of_code=result.lines_of_code,
            error_message=result.error_message,
        )
        self.experiment_log.log_experiment(experiment)
    
    async def print_summary(self):
        """Print summary of improvement session."""
        stats = self.experiment_log.get_statistics()
        
        logger.info("\n" + "="*60)
        logger.info("EXPERIMENT SUMMARY")
        logger.info("="*60)
        logger.info(f"Skill: {self.skill_name}")
        logger.info(f"Experiment ID: {self.experiment_id}")
        logger.info(f"Total iterations: {stats.get('total_experiments', 0)}")
        logger.info(f"Kept: {stats.get('kept', 0)}")
        logger.info(f"Discarded: {stats.get('discarded', 0)}")
        logger.info(f"Crashed: {stats.get('crashed', 0)}")
        logger.info(f"Success rate: {stats.get('success_rate', 0):.1%}")
        logger.info(f"Best metric: {stats.get('best_metric', 0):.6f}")
        logger.info(f"Total improvement: {stats.get('improvement_percentage', 0):.2f}%")
        logger.info("="*60)
    
    async def _load_skill(self):
        """Load the skill object for evaluation."""
        # Placeholder: would dynamically import and instantiate the skill
        # For now, return a mock object
        return None
    
    async def _read_skill_code(self) -> str:
        """Read current skill code."""
        with open(self.skill_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def _write_skill_code(self, code: str):
        """Write skill code."""
        with open(self.skill_path, 'w', encoding='utf-8') as f:
            f.write(code)
