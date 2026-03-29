# -*- coding: utf-8 -*-
"""
Agent-level self-improvement system.
Enables autonomous improvement of agent behavior and decision-making.
"""

import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from .config import ImprovementConfig, ImprovementPolicy
from .evaluator import Evaluator, EvaluationResult, AgentTestSuite
from .experiment import Experiment, ExperimentLog, GitManager

logger = logging.getLogger(__name__)


class AgentSelfImprover:
    """
    Self-improvement at the agent level.
    
    Optimizes agent-level behavior including:
    - Skill selection strategy
    - Context management
    - Memory compaction rules
    - Error handling patterns
    - Multi-agent coordination
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_config_path: str,
        test_suite: AgentTestSuite,
        config: ImprovementConfig,
        policy: Optional[ImprovementPolicy] = None,
    ):
        self.agent_id = agent_id
        self.agent_config_path = Path(agent_config_path)
        self.test_suite = test_suite
        self.config = config
        self.policy = policy or ImprovementPolicy()
        
        # Experiment management
        self.experiment_id = f"agent_{agent_id}_{int(time.time())}"
        self.branch_name = f"{config.experiment_branch_prefix}/agent/{agent_id}/{int(time.time())}"
        
        # Setup logging
        log_dir = Path(f"experiments/{self.experiment_id}")
        self.experiment_log = ExperimentLog(str(log_dir), self.experiment_id)
        
        # Git management
        if config.git_enabled:
            self.git = GitManager(".")
        else:
            self.git = None
        
        # Evaluator
        self.evaluator = Evaluator(test_suite)
        
        # State
        self.baseline: Optional[EvaluationResult] = None
        self.current_best: Optional[EvaluationResult] = None
        self.iteration = 0
        self.consecutive_crashes = 0
        
        logger.info(f"Initialized AgentSelfImprover for agent {agent_id}")
    
    async def run_improvement_loop(self, max_iterations: Optional[int] = None):
        """
        Main improvement loop for agent optimization.
        
        Similar to skill improvement but operates at agent level:
        - Modifies agent configuration
        - Runs benchmark scenarios
        - Evaluates aggregate performance
        - Keeps or discards changes
        
        Args:
            max_iterations: Maximum iterations (None = infinite)
        """
        # Initialize
        if not await self._initialize_experiment():
            logger.error("Failed to initialize experiment")
            return
        
        # Establish baseline
        await self._establish_baseline()
        
        # Determine iteration limit
        iterations = max_iterations or self.config.max_iterations
        
        logger.info("Starting agent improvement loop...")
        
        # Main loop
        while iterations is None or self.iteration < iterations:
            self.iteration += 1
            
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Agent Improvement - Iteration {self.iteration}")
                logger.info(f"{'='*60}")
                
                # Generate hypothesis for agent improvement
                hypothesis = await self._generate_agent_hypothesis()
                logger.info(f"Hypothesis: {hypothesis['description']}")
                
                # Store previous config
                previous_config = await self._read_config()
                
                # Apply modification
                await self._modify_agent_config(hypothesis)
                
                # Commit
                commit_hash = None
                if self.git and self.config.auto_commit:
                    commit_hash = self.git.commit(f"Agent improvement {self.iteration}: {hypothesis['description']}")
                else:
                    commit_hash = f"agent_iter_{self.iteration}"
                
                # Run benchmark
                result = await self._run_agent_benchmark()
                
                # Decide
                decision = self._make_decision(result)
                logger.info(f"Decision: {decision}")
                
                # Log
                await self._log_experiment(commit_hash, result, decision, hypothesis)
                
                # Handle decision
                if decision == "keep":
                    self.current_best = result
                    self.consecutive_crashes = 0
                    logger.info(f"✓ Agent improvement kept! New score: {result.metric_value:.6f}")
                elif decision == "crash":
                    self.consecutive_crashes += 1
                    logger.warning(f"✗ Experiment crashed")
                    await self._revert_config(previous_config)
                    
                    if self.consecutive_crashes >= self.config.crash_tolerance:
                        logger.error("Too many crashes, stopping")
                        break
                else:  # discard
                    self.consecutive_crashes = 0
                    logger.info(f"✗ Change discarded")
                    await self._revert_config(previous_config)
                
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in improvement loop: {e}", exc_info=True)
                self.consecutive_crashes += 1
                if self.consecutive_crashes >= self.config.crash_tolerance:
                    break
        
        await self._print_summary()
    
    async def _initialize_experiment(self) -> bool:
        """Initialize agent experiment."""
        logger.info(f"Initializing agent improvement for {self.agent_id}")
        
        if not self.agent_config_path.exists():
            logger.error(f"Agent config not found: {self.agent_config_path}")
            return False
        
        if not self.policy.is_file_allowed(str(self.agent_config_path)):
            logger.error(f"Policy does not allow modifying: {self.agent_config_path}")
            return False
        
        if self.git and self.config.git_enabled:
            if not self.git.create_branch(self.branch_name):
                logger.warning("Could not create git branch")
                self.git = None
        
        return True
    
    async def _establish_baseline(self) -> EvaluationResult:
        """Establish baseline agent performance."""
        logger.info("Establishing agent baseline...")
        
        agent = await self._load_agent()
        result = await self.evaluator.evaluate(agent, self.config.time_budget_seconds)
        
        self.baseline = result
        self.current_best = result
        
        # Log baseline
        commit_hash = self.git.get_current_commit() if self.git else "baseline"
        experiment = Experiment(
            commit_hash=commit_hash,
            experiment_id=f"{self.experiment_id}_0",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            hypothesis="agent baseline",
            strategy="baseline",
            metric_value=result.metric_value,
            metric_name=result.metric_name,
            memory_gb=result.memory_mb / 1024,
            execution_time=result.execution_time_seconds,
            status="keep",
            tests_passed=result.tests_passed,
            tests_total=result.tests_total,
        )
        self.experiment_log.log_experiment(experiment)
        
        logger.info(f"Agent baseline: {result.metric_name}={result.metric_value:.6f}")
        return result
    
    async def _generate_agent_hypothesis(self) -> Dict[str, Any]:
        """
        Generate hypothesis for agent improvement.
        
        Areas to optimize:
        - Skill selection strategy
        - Context window management
        - Memory compaction
        - Error handling
        - Multi-agent coordination
        """
        # Placeholder implementation
        optimization_areas = [
            "skill_selection",
            "context_management",
            "memory_compaction",
            "error_handling",
            "coordination",
        ]
        
        area = optimization_areas[self.iteration % len(optimization_areas)]
        
        return {
            "description": f"Optimize {area}",
            "strategy": "agent_optimization",
            "area": area,
            "modifications": {},
        }
    
    async def _modify_agent_config(self, hypothesis: Dict[str, Any]):
        """Apply modifications to agent configuration."""
        # Placeholder: would modify agent config based on hypothesis
        logger.info(f"Modifying agent config: {hypothesis['description']}")
        pass
    
    async def _run_agent_benchmark(self) -> EvaluationResult:
        """Run agent through benchmark scenarios."""
        agent = await self._load_agent()
        result = await self.evaluator.evaluate(agent, self.config.time_budget_seconds)
        return result
    
    def _make_decision(self, result: EvaluationResult) -> str:
        """Decide whether to keep or discard agent changes."""
        return self.evaluator.compare_results(
            result,
            self.current_best,
            threshold=self.config.improvement_threshold
        )
    
    async def _log_experiment(
        self,
        commit_hash: str,
        result: EvaluationResult,
        decision: str,
        hypothesis: Dict[str, Any]
    ):
        """Log agent experiment."""
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
            tests_passed=result.tests_passed,
            tests_total=result.tests_total,
            error_message=result.error_message,
        )
        self.experiment_log.log_experiment(experiment)
    
    async def _load_agent(self):
        """Load agent for evaluation."""
        # Placeholder: would load and instantiate the agent
        return None
    
    async def _read_config(self) -> Dict[str, Any]:
        """Read current agent configuration."""
        import json
        with open(self.agent_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def _write_config(self, config: Dict[str, Any]):
        """Write agent configuration."""
        import json
        with open(self.agent_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    async def _revert_config(self, config: Dict[str, Any]):
        """Revert to previous configuration."""
        await self._write_config(config)
    
    async def _print_summary(self):
        """Print agent improvement summary."""
        stats = self.experiment_log.get_statistics()
        
        logger.info("\n" + "="*60)
        logger.info("AGENT IMPROVEMENT SUMMARY")
        logger.info("="*60)
        logger.info(f"Agent: {self.agent_id}")
        logger.info(f"Total iterations: {stats.get('total_experiments', 0)}")
        logger.info(f"Improvements kept: {stats.get('kept', 0)}")
        logger.info(f"Overall improvement: {stats.get('improvement_percentage', 0):.2f}%")
        logger.info("="*60)
