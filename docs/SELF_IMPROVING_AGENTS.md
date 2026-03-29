# Self-Improving Agent Architecture for DominusPrime

## Executive Summary

This document analyzes the autoresearch self-improvement mechanism (by Andrej Karpathy) and proposes how to implement similar capabilities into DominusPrime agents, enabling them to autonomously improve their own performance through iterative experimentation.

## Understanding Autoresearch's Self-Improvement Model

### Core Mechanism

Autoresearch implements a **continuous autonomous research loop** where an AI agent:

1. **Modifies code** (makes an experimental change)
2. **Runs an experiment** (trains for fixed time budget)
3. **Evaluates results** (measures against fixed metric)
4. **Decides to keep or discard** (based on objective improvement)
5. **Repeats indefinitely** (until manually stopped)

### Key Design Principles

#### 1. Single Point of Modification
- **Autoresearch**: Only `train.py` is modified (model, optimizer, training loop)
- **Benefits**: 
  - Manageable scope for the agent
  - Reviewable diffs
  - Clear cause-and-effect relationships
  - Reduced complexity and debugging surface

#### 2. Fixed Evaluation Metric
- **Autoresearch**: `val_bpb` (validation bits per byte) - vocabulary-size-independent
- **Benefits**:
  - Objective, unambiguous comparison
  - Fair evaluation across different architectural changes
  - No gaming the metric through vocabulary manipulation

#### 3. Fixed Time Budget
- **Autoresearch**: Exactly 5 minutes of training time
- **Benefits**:
  - Experiments directly comparable regardless of changes
  - Optimizes for the constraint (real-world relevant)
  - Predictable experiment duration (~12 experiments/hour)

#### 4. Git-Based Version Control
- **Autoresearch**: Every experiment is a git commit
- **Benefits**:
  - Easy rollback to any previous state
  - Complete experiment history
  - Ability to branch and explore different directions
  - Clear lineage of improvements

#### 5. Autonomous Continuous Operation
- **Autoresearch**: Runs indefinitely without human intervention
- **Benefits**:
  - ~100 experiments overnight while human sleeps
  - No bottleneck on human availability
  - Explores large solution space efficiently

#### 6. Simplicity Bias
- **Autoresearch**: Simpler code preferred; removing code while maintaining results is valuable
- **Benefits**:
  - Prevents complexity accumulation
  - Encourages generalizable solutions
  - Maintains code quality over time

### The Experiment Loop (Detailed)

```
INITIALIZE:
1. Create dedicated experiment branch (e.g., autoresearch/mar29)
2. Read all context files (README, code to modify, constraints)
3. Create results.tsv for logging
4. Run baseline to establish starting performance

LOOP FOREVER:
1. Analyze current state (git commit, previous results)
2. Generate experimental hypothesis
3. Modify target file based on hypothesis
4. Git commit with descriptive message
5. Run experiment (redirect output to run.log)
6. Extract metrics from log
7. Record to results.tsv (commit hash, metric, memory, status, description)
8. If improved: Keep commit (advance branch)
   If equal/worse: Git reset to previous state
   If crashed: Attempt fix or skip
9. Generate next hypothesis based on accumulated knowledge
10. Repeat (NEVER ask for permission to continue)
```

### Experiment Logging Format

```tsv
commit	val_bpb	memory_gb	status	description
a1b2c3d	0.997900	44.0	keep	baseline
b2c3d4e	0.993200	44.2	keep	increase LR to 0.04
c3d4e5f	1.005000	44.0	discard	switch to GeLU activation
d4e5f6g	0.000000	0.0	crash	double model width (OOM)
```

## Implementation Strategy for DominusPrime

### Phase 1: Foundation (Skill-Level Self-Improvement)

Start with **skill self-improvement** - agents improve their own skill implementations.

#### Architecture

```python
# New file: src/dominusprime/agents/self_improvement/skill_improver.py

class SkillSelfImprover:
    """
    Autonomous self-improvement for individual skills.
    Similar to autoresearch but for skill code optimization.
    """
    
    def __init__(self, skill_name: str, config: ImprovementConfig):
        self.skill_name = skill_name
        self.skill_path = f"src/dominusprime/agents/skills/{skill_name}.py"
        self.test_path = f"tests/skills/test_{skill_name}.py"
        self.config = config
        self.experiment_branch = f"improve/{skill_name}/{timestamp}"
        
    async def run_improvement_loop(self):
        """
        Main improvement loop - runs until manually stopped.
        """
        await self.initialize_experiment()
        baseline = await self.establish_baseline()
        
        iteration = 0
        while True:  # Autonomous continuous operation
            iteration += 1
            
            # Generate hypothesis from previous experiments
            hypothesis = await self.generate_hypothesis(iteration)
            
            # Modify skill code
            await self.apply_modification(hypothesis)
            
            # Commit change
            commit_hash = await self.git_commit(hypothesis.description)
            
            # Run evaluation
            result = await self.evaluate_skill()
            
            # Decide: keep or discard
            decision = self.decide_outcome(result, baseline)
            
            # Log result
            await self.log_experiment(commit_hash, result, decision, hypothesis)
            
            if decision == "keep":
                baseline = result
                logger.info(f"✓ Improvement kept: {result.metric}")
            else:
                await self.git_reset()
                logger.info(f"✗ Change discarded: {result.metric}")
            
            # Optional: brief pause to avoid rate limits
            await asyncio.sleep(1)
```

#### Evaluation Metrics by Skill Type

Different skills need different fixed evaluation metrics:

**1. Information Retrieval Skills** (search, scraping, etc.)
- **Metric**: Retrieval F1 score on test dataset
- **Fixed Budget**: 30 seconds execution time
- **Test Data**: Curated Q&A pairs with ground truth answers

**2. Task Completion Skills** (calendar, email, file ops, etc.)
- **Metric**: Task success rate on test suite
- **Fixed Budget**: 5 test cases, 60 seconds total
- **Test Data**: Standardized task scenarios with expected outcomes

**3. Conversational Skills** (response generation, etc.)
- **Metric**: Combined score (relevance + coherence + helpfulness)
- **Fixed Budget**: 20 test interactions
- **Test Data**: Conversation scenarios with human-rated reference responses

**4. Code Generation Skills**
- **Metric**: Test pass rate + code quality score
- **Fixed Budget**: Generate 10 solutions, run tests
- **Test Data**: Programming challenges with test suites

#### Implementation Config

```python
@dataclass
class ImprovementConfig:
    """Configuration for self-improvement experiments."""
    
    # Evaluation
    metric_name: str  # e.g., "f1_score", "success_rate", "bits_per_byte"
    time_budget_seconds: int  # fixed time budget for experiments
    evaluation_samples: int  # number of test cases
    
    # Experiment management
    max_iterations: Optional[int] = None  # None = infinite
    git_enabled: bool = True
    auto_commit: bool = True
    
    # Decision criteria
    improvement_threshold: float = 0.001  # minimum improvement to keep
    simplicity_bonus: float = 0.01  # bonus for code reduction
    
    # Safety
    max_memory_mb: int = 4096
    crash_tolerance: int = 3  # max consecutive crashes before stopping
    
    # Agent configuration
    llm_model: str = "claude-sonnet-4"
    temperature: float = 0.7
    context_window: int = 100000  # for reading code/history
```

### Phase 2: Agent-Level Self-Improvement

Expand to **full agent self-improvement** - agents optimize their own behavior, decision-making, and skill selection.

#### Architecture

```python
# New file: src/dominusprime/agents/self_improvement/agent_improver.py

class AgentSelfImprover:
    """
    Self-improvement at the agent level.
    Optimizes: skill selection, decision-making, context management, etc.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.agent_config_path = f"agents/{agent_id}/config.yaml"
        self.experiment_branch = f"improve/agent/{agent_id}/{timestamp}"
        
    async def run_improvement_loop(self):
        """
        Optimize agent-level behavior through interaction simulation.
        """
        await self.initialize_experiment()
        baseline = await self.run_agent_benchmark()
        
        iteration = 0
        while True:
            iteration += 1
            
            # Areas to optimize:
            # 1. Skill selection strategy
            # 2. Context window management
            # 3. Memory compaction rules
            # 4. Error handling patterns
            # 5. Multi-agent coordination
            
            hypothesis = await self.generate_agent_hypothesis(iteration)
            await self.modify_agent_config(hypothesis)
            
            commit_hash = await self.git_commit(hypothesis.description)
            result = await self.run_agent_benchmark()
            
            decision = self.decide_outcome(result, baseline)
            await self.log_experiment(commit_hash, result, decision, hypothesis)
            
            if decision == "keep":
                baseline = result
            else:
                await self.git_reset()
            
            await asyncio.sleep(5)
```

#### Agent Benchmarking

```python
class AgentBenchmark:
    """
    Fixed benchmark suite for agent evaluation.
    Similar to how autoresearch has fixed eval data.
    """
    
    def __init__(self):
        self.scenarios = self.load_benchmark_scenarios()
        
    def load_benchmark_scenarios(self) -> List[Scenario]:
        """
        Load standardized scenarios for agent evaluation.
        Each scenario has:
        - Initial state
        - User request
        - Expected outcome
        - Success criteria
        """
        return [
            Scenario(
                name="multi_step_task",
                initial_state={...},
                user_request="Schedule meeting and send summary",
                expected_outcome={...},
                success_criteria=["meeting_scheduled", "email_sent"],
                time_budget=120,
            ),
            # ... more scenarios
        ]
    
    async def evaluate_agent(self, agent: Agent) -> BenchmarkResult:
        """
        Run agent through all benchmark scenarios.
        Returns aggregate metrics.
        """
        results = []
        for scenario in self.scenarios:
            result = await self.run_scenario(agent, scenario)
            results.append(result)
        
        return BenchmarkResult(
            success_rate=self.compute_success_rate(results),
            avg_time=self.compute_avg_time(results),
            skill_efficiency=self.compute_skill_efficiency(results),
            user_satisfaction=self.compute_satisfaction(results),
            total_score=self.compute_total_score(results),
        )
```

### Phase 3: Meta-Improvement (Self-Improving Self-Improvement)

The ultimate level: **the improvement process improves itself**.

```python
class MetaImprover:
    """
    Optimizes the self-improvement process itself.
    Modifies: hypothesis generation, evaluation criteria, decision logic.
    """
    
    async def improve_improvement_process(self):
        """
        Self-improvement loop for the improvement system.
        Meta-metric: Rate of improvement over time.
        """
        baseline_improvement_rate = await self.measure_improvement_rate()
        
        while True:
            # Modify the improvement process
            hypothesis = await self.generate_meta_hypothesis()
            
            # e.g., "Try generating more radical hypotheses"
            # e.g., "Adjust improvement threshold dynamically"
            # e.g., "Use ensemble evaluation instead of single metric"
            
            await self.modify_improvement_config(hypothesis)
            
            # Evaluate by running improvement cycles
            new_improvement_rate = await self.measure_improvement_rate()
            
            if new_improvement_rate > baseline_improvement_rate:
                baseline_improvement_rate = new_improvement_rate
            else:
                await self.revert_config()
```

## Integration with DominusPrime Architecture

### 1. Skill System Integration

```python
# Extend existing skill base class
# File: src/dominusprime/agents/skills/base.py

class Skill:
    """Base class for all skills (existing)."""
    
    # NEW: Self-improvement interface
    def enable_self_improvement(self, config: ImprovementConfig):
        """Enable autonomous self-improvement for this skill."""
        self.improver = SkillSelfImprover(
            skill_name=self.__class__.__name__,
            config=config
        )
        return self.improver
    
    # NEW: Provide test suite for evaluation
    def get_test_suite(self) -> TestSuite:
        """Return standardized test suite for evaluation."""
        raise NotImplementedError("Skills must implement get_test_suite")
    
    # NEW: Self-evaluation
    async def self_evaluate(self) -> EvaluationResult:
        """Run self-evaluation and return metrics."""
        test_suite = self.get_test_suite()
        return await test_suite.run_evaluation(self)
```

### 2. Agent Framework Integration

```python
# File: src/dominusprime/agents/__init__.py

class DominusPrimeAgent:
    """Main agent class (existing)."""
    
    # NEW: Self-improvement capabilities
    async def enable_self_improvement(
        self, 
        mode: str = "skill",  # "skill", "agent", or "meta"
        config: Optional[ImprovementConfig] = None
    ):
        """
        Enable self-improvement mode.
        
        Args:
            mode: Level of self-improvement
                - "skill": Improve individual skills
                - "agent": Improve agent-level behavior
                - "meta": Improve the improvement process
            config: Configuration for improvement experiments
        """
        if mode == "skill":
            # Allow agent to improve its skills
            for skill in self.skills:
                if hasattr(skill, 'enable_self_improvement'):
                    improver = skill.enable_self_improvement(config)
                    await improver.run_improvement_loop()
        
        elif mode == "agent":
            # Improve agent-level behavior
            improver = AgentSelfImprover(self.agent_id)
            await improver.run_improvement_loop()
        
        elif mode == "meta":
            # Improve the improvement process
            meta_improver = MetaImprover(self)
            await meta_improver.improve_improvement_process()
```

### 3. CLI Integration

```bash
# New commands for self-improvement

# Start skill improvement
dominusprime improve skill --name web_search --iterations 100

# Start agent improvement
dominusprime improve agent --agent-id main_agent --continuous

# Start meta-improvement
dominusprime improve meta --experiment-name optimize_optimization

# View improvement history
dominusprime improve history --skill web_search

# Rollback to previous version
dominusprime improve rollback --skill web_search --commit abc123f
```

### 4. Monitoring Dashboard

Add a new section to the console UI for monitoring self-improvement:

```typescript
// File: console/src/pages/SelfImprovement/index.tsx

export function SelfImprovementDashboard() {
  return (
    <div>
      <h2>Self-Improvement Experiments</h2>
      
      {/* Live experiment status */}
      <ExperimentStatus />
      
      {/* Performance over time */}
      <ImprovementChart />
      
      {/* Recent experiments log */}
      <ExperimentLog />
      
      {/* Current vs baseline comparison */}
      <PerformanceComparison />
      
      {/* Control panel */}
      <ImprovementControls />
    </div>
  );
}
```

## Implementation Roadmap

### Milestone 1: Basic Infrastructure (2 weeks)
- [ ] Create `self_improvement` module structure
- [ ] Implement `ImprovementConfig` and base classes
- [ ] Add git integration utilities
- [ ] Create experiment logging system
- [ ] Build evaluation framework

### Milestone 2: Skill-Level Improvement (4 weeks)
- [ ] Implement `SkillSelfImprover`
- [ ] Create test suites for existing skills
- [ ] Add evaluation metrics for each skill type
- [ ] Build hypothesis generation system
- [ ] Integrate with skill base class
- [ ] Add CLI commands

### Milestone 3: Agent-Level Improvement (4 weeks)
- [ ] Implement `AgentSelfImprover`
- [ ] Create agent benchmark suite
- [ ] Build agent evaluation metrics
- [ ] Integrate with agent framework
- [ ] Add monitoring dashboard

### Milestone 4: Meta-Improvement (6 weeks)
- [ ] Implement `MetaImprover`
- [ ] Build meta-evaluation metrics
- [ ] Add improvement rate tracking
- [ ] Optimize hypothesis generation
- [ ] Fine-tune decision criteria

### Milestone 5: Production Readiness (4 weeks)
- [ ] Add safety guardrails
- [ ] Implement resource limits
- [ ] Add experiment sandboxing
- [ ] Build rollback mechanisms
- [ ] Create comprehensive documentation
- [ ] Add telemetry and monitoring

## Safety and Governance

### Safety Measures

1. **Sandboxing**: Run experiments in isolated environments
2. **Resource Limits**: Hard caps on memory, CPU, time
3. **Human Oversight**: Critical changes require approval
4. **Rollback Mechanism**: Instant revert to any previous state
5. **Kill Switch**: Emergency stop for all improvement processes

### Governance

```python
@dataclass
class ImprovementPolicy:
    """Governance policy for self-improvement."""
    
    # What can be modified
    allowed_files: List[str]
    forbidden_patterns: List[str]  # Regex patterns to never modify
    
    # Approval requirements
    require_human_approval_for: List[str]  # e.g., ["security", "data_access"]
    
    # Resource limits
    max_memory_mb: int
    max_cpu_percent: int
    max_experiments_per_day: int
    
    # Monitoring
    alert_on_performance_drop: bool
    alert_threshold: float
    log_all_changes: bool
```

## Expected Benefits

1. **Continuous Improvement**: Agents get better over time without human intervention
2. **Adaptation**: Agents adapt to changing requirements and environments
3. **Scale**: Multiple agents can improve in parallel
4. **Learning Transfer**: Improvements in one skill can inform others
5. **Human Augmentation**: Humans focus on strategy, agents handle optimization

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Agents break themselves | Sandboxing, automated rollback, baseline preservation |
| Resource exhaustion | Hard limits, monitoring, rate limiting |
| Metric gaming | Multiple evaluation metrics, simplicity bias |
| Unintended behavior | Human oversight for critical changes, audit logs |
| Infinite loops | Iteration limits, progress tracking, kill switch |
| Code quality degradation | Simplicity preference, code review tools |

## Conclusion

By implementing autoresearch-style self-improvement in DominusPrime, we can create agents that:

1. **Autonomously improve** their own capabilities
2. **Learn from experience** through systematic experimentation
3. **Optimize for real constraints** (time, resources, accuracy)
4. **Maintain code quality** through simplicity bias
5. **Scale improvement** across multiple agents and skills

This transforms DominusPrime from a static personal assistant into a **continuously evolving AI system** that grows more capable over time.

## References

- Autoresearch Repository: https://github.com/karpathy/autoresearch
- Karpathy's Tweet Thread: https://x.com/karpathy/status/2029701092347630069
- Related: Constitutional AI, RLHF, Self-Play, Meta-Learning

## Next Steps

1. Review and approve this design document
2. Create detailed technical specifications
3. Set up experiment infrastructure
4. Begin Milestone 1 implementation
5. Run pilot experiments with one skill
6. Iterate based on results
7. Scale to full agent framework
