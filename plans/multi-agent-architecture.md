# Multi-Agent Spawning Architecture

## Overview

Design and implementation plan for adding multi-agent task decomposition and delegation capabilities to DominusPrime v0.9.3.

**Goal**: Enable DominusPrime to automatically spawn specialized sub-agents for complex tasks, coordinate their work, and aggregate results back to the user.

## Current Architecture Analysis

### Existing Components

1. **DominusPrimeAgent** (`src/dominusprime/agents/react_agent.py`)
   - Extends AgentScope's `ReActAgent`
   - Integrated tools: shell, file I/O, browser, desktop screenshot
   - Dynamic skill loading from working directory
   - Memory management with auto-compaction
   - Session state persistence

2. **AgentRunner** (`src/dominusprime/app/runner/runner.py`)
   - Handles agent queries and lifecycle
   - Manages session state (load/save)
   - Coordinates with ChatManager
   - MCP client integration

3. **Tools & Skills System**
   - Built-in tools via Toolkit registration
   - Skill discovery from `~/.dominusprime/active_skills/`
   - Extensible via MCP clients

4. **Memory Management**
   - MemoryManager with ReMeCopaw integration
   - Auto-compaction hooks
   - Context window management (up to 128K tokens)

## Multi-Agent System Design

### 1. Task Complexity Detection

**Component**: `TaskComplexityAnalyzer`

```python
class TaskComplexityAnalyzer:
    """Analyzes user queries to determine if task decomposition is beneficial."""
    
    def analyze(self, query: str, context: List[Msg]) -> TaskComplexity:
        """
        Analyze task complexity based on:
        - Multiple distinct objectives
        - Sequential dependencies
        - Different skill domains required
        - Estimated execution time
        - Resource requirements
        """
```

**Complexity Indicators**:
- **Simple**: Single action, one tool/skill (e.g., "read file.txt")
- **Moderate**: Multiple related actions (e.g., "search web and summarize top 3 results")
- **Complex**: Multiple independent subtasks (e.g., "research topic X, write report, create presentation")
- **Very Complex**: Multi-domain, long-running (e.g., "build full-stack app with tests and docs")

**Detection Strategy**:
```python
indicators = {
    "multiple_objectives": ["and", "then", "also", "additionally"],
    "sequential_steps": ["first", "next", "after that", "finally"],
    "parallel_tasks": ["simultaneously", "in parallel", "at the same time"],
    "domain_diversity": ["web scraping", "file processing", "data analysis"],
}
```

### 2. Task Decomposition Strategy

**Component**: `TaskDecomposer`

```python
class TaskDecomposer:
    """Breaks down complex tasks into manageable subtasks."""
    
    def decompose(
        self,
        query: str,
        complexity: TaskComplexity,
        context: List[Msg]
    ) -> List[SubTask]:
        """
        Decomposition strategies:
        1. Sequential: Tasks must run in order (T1 → T2 → T3)
        2. Parallel: Independent tasks (T1 || T2 || T3)
        3. Hybrid: Mix of sequential and parallel
        """
```

**Subtask Structure**:
```python
@dataclass
class SubTask:
    id: str  # Unique identifier
    description: str  # What needs to be done
    dependencies: List[str]  # IDs of required preceding tasks
    required_tools: List[str]  # Tools needed
    required_skills: List[str]  # Skills needed
    estimated_complexity: str  # simple|moderate|complex
    execution_mode: str  # sequential|parallel
    timeout: int  # Max execution time (seconds)
```

**Decomposition Approach**:
1. Use LLM to parse user intent
2. Identify distinct objectives
3. Determine dependencies
4. Group by skill domain
5. Create execution plan

### 3. Sub-Agent Spawning Mechanism

**Component**: `AgentOrchestrator`

```python
class AgentOrchestrator:
    """Manages lifecycle of sub-agents."""
    
    async def spawn_agent(
        self,
        subtask: SubTask,
        context: AgentContext
    ) -> SubAgent:
        """
        Spawn specialized sub-agent:
        1. Create isolated agent instance
        2. Configure with required tools/skills
        3. Set limited context (subtask-specific)
        4. Assign timeout and resource limits
        """
    
    async def execute_parallel(
        self,
        subtasks: List[SubTask]
    ) -> List[TaskResult]:
        """Execute independent subtasks in parallel."""
    
    async def execute_sequential(
        self,
        subtasks: List[SubTask]
    ) -> List[TaskResult]:
        """Execute dependent subtasks in sequence."""
```

**Sub-Agent Characteristics**:
- **Isolation**: Own memory space, separate from main agent
- **Specialization**: Only tools/skills needed for subtask
- **Limited Scope**: Can only see subtask context, not full conversation
- **Resource Limits**: Timeout, max iterations, token budget
- **Focused Prompt**: Task-specific system prompt

**Agent Pool Management**:
```python
class AgentPool:
    """Manage reusable sub-agent instances."""
    
    max_concurrent_agents: int = 5  # Configurable
    agent_timeout: int = 300  # 5 minutes default
    
    async def get_agent(self, spec: AgentSpec) -> SubAgent:
        """Get or create agent matching specification."""
    
    async def release_agent(self, agent: SubAgent):
        """Return agent to pool or destroy if over limit."""
```

### 4. Agent-to-Agent Communication Protocol

**Component**: `AgentCommunicationBus`

```python
class AgentCommunicationBus:
    """Message passing between main agent and sub-agents."""
    
    async def send_to_subagent(
        self,
        agent_id: str,
        message: AgentMessage
    ):
        """Send instruction or data to sub-agent."""
    
    async def receive_from_subagent(
        self,
        agent_id: str
    ) -> AgentMessage:
        """Receive progress update or result from sub-agent."""
    
    async def broadcast_to_all(self, message: AgentMessage):
        """Send message to all active sub-agents."""
```

**Message Types**:
```python
@dataclass
class AgentMessage:
    type: str  # task_assignment | progress_update | result | error | query
    sender_id: str
    receiver_id: str
    content: Any
    timestamp: datetime
    metadata: dict

# Example message flow:
# Main → Sub: TaskAssignment(subtask_details)
# Sub → Main: ProgressUpdate(status, percentage)
# Sub → Main: Query(clarification_needed)
# Main → Sub: Response(answer)
# Sub → Main: Result(output, artifacts)
```

### 5. Result Aggregation and Reporting

**Component**: `ResultAggregator`

```python
class ResultAggregator:
    """Combines sub-agent results into coherent response."""
    
    async def aggregate(
        self,
        subtask_results: List[TaskResult],
        original_query: str
    ) -> AggregatedResult:
        """
        Aggregation strategies:
        1. Sequential narrative (for ordered tasks)
        2. Parallel summary (for independent tasks)
        3. Hierarchical structure (for complex dependencies)
        """
    
    async def format_for_user(
        self,
        result: AggregatedResult,
        format: str = "conversational"
    ) -> str:
        """Format aggregated result for user presentation."""
```

**Result Structure**:
```python
@dataclass
class TaskResult:
    subtask_id: str
    status: str  # success | partial_success | failure
    output: Any  # Main result
    artifacts: List[str]  # Files created, URLs visited, etc.
    execution_time: float
    errors: List[str]
    logs: str

@dataclass
class AggregatedResult:
    overall_status: str
    summary: str  # High-level overview
    detailed_results: List[TaskResult]
    combined_artifacts: List[str]
    total_execution_time: float
    recommendations: List[str]  # Next steps, issues found, etc.
```

### 6. Memory and Context Management

**Strategy**:

1. **Main Agent Memory**: Full conversation history
2. **Sub-Agent Memory**: 
   - Subtask description
   - Relevant context from main conversation
   - Own execution history
   - No access to other sub-agent memories

3. **Shared Knowledge Base**:
   - Facts discovered by any agent
   - Written to working directory files
   - Available to all agents via file tools

**Context Passing**:
```python
class ContextManager:
    """Manages context distribution to sub-agents."""
    
    def extract_relevant_context(
        self,
        subtask: SubTask,
        full_history: List[Msg],
        max_tokens: int = 4096
    ) -> List[Msg]:
        """
        Extract only relevant messages:
        1. User messages related to subtask
        2. Previous results from dependency tasks
        3. Key facts from main conversation
        """
    
    def merge_subagent_learnings(
        self,
        main_memory: InMemoryMemory,
        subagent_results: List[TaskResult]
    ):
        """Add sub-agent discoveries to main agent memory."""
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DominusPrimeAgent (Main)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │        TaskComplexityAnalyzer                             │   │
│  │  • Analyzes query complexity                              │   │
│  │  • Determines if delegation needed                        │   │
│  └─────────────────┬────────────────────────────────────────┘   │
│                    │                                             │
│         ┌──────────▼──────────┐                                 │
│         │  Simple Task?       │                                 │
│         └──┬────────────────┬─┘                                 │
│      YES   │                │ NO                                │
│    ┌───────▼──┐     ┌───────▼──────────────────┐               │
│    │ Execute  │     │  TaskDecomposer           │               │
│    │ Directly │     │  • Break into subtasks    │               │
│    └──────────┘     │  • Identify dependencies  │               │
│                     │  • Create execution plan  │               │
│                     └───────┬──────────────────┘               │
│                             │                                   │
│                     ┌───────▼──────────────────┐               │
│                     │  AgentOrchestrator        │               │
│                     │  • Spawn sub-agents       │               │
│                     │  • Manage execution       │               │
│                     └───────┬──────────────────┘               │
└─────────────────────────────┼───────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
      ┌───────▼────┐  ┌──────▼─────┐  ┌─────▼──────┐
      │ SubAgent 1 │  │ SubAgent 2 │  │ SubAgent 3 │
      │ (Research) │  │  (Write)   │  │  (Review)  │
      └───────┬────┘  └──────┬─────┘  └─────┬──────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                      ┌───────▼──────────────┐
                      │  ResultAggregator     │
                      │  • Combine results    │
                      │  • Format response    │
                      └───────┬──────────────┘
                              │
                      ┌───────▼──────────────┐
                      │    User Response      │
                      └──────────────────────┘
```

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

1. **Create Agent Orchestration Framework**
   - [ ] Implement `AgentOrchestrator` class
   - [ ] Implement `AgentPool` for sub-agent lifecycle
   - [ ] Create `SubAgent` wrapper class
   - [ ] Add configuration options to `config.yaml`

2. **Build Communication Layer**
   - [ ] Implement `AgentCommunicationBus`
   - [ ] Define message protocols
   - [ ] Add message queue/event system
   - [ ] Create inter-agent messaging tests

### Phase 2: Task Analysis & Decomposition (Week 3)

3. **Task Complexity Detection**
   - [ ] Implement `TaskComplexityAnalyzer`
   - [ ] Create complexity scoring algorithm
   - [ ] Add LLM-based intent parsing
   - [ ] Build test suite with sample queries

4. **Task Decomposition Engine**
   - [ ] Implement `TaskDecomposer`
   - [ ] Create dependency graph builder
   - [ ] Add sequential/parallel execution planner
   - [ ] Test with complex multi-step tasks

### Phase 3: Execution & Coordination (Week 4)

5. **Sub-Agent Execution**
   - [ ] Implement parallel execution engine
   - [ ] Implement sequential execution engine
   - [ ] Add timeout and resource management
   - [ ] Create progress tracking system

6. **Context Management**
   - [ ] Implement `ContextManager`
   - [ ] Build context extraction logic
   - [ ] Add memory isolation per sub-agent
   - [ ] Create context merging system

### Phase 4: Result Handling (Week 5)

7. **Result Aggregation**
   - [ ] Implement `ResultAggregator`
   - [ ] Create result formatting templates
   - [ ] Add error handling and partial results
   - [ ] Build user-friendly reporting

8. **Integration with Main Agent**
   - [ ] Integrate orchestrator into `DominusPrimeAgent`
   - [ ] Add decision logic to `AgentRunner`
   - [ ] Update system prompts
   - [ ] Add user controls (/delegate command)

### Phase 5: Testing & Optimization (Week 6)

9. **Comprehensive Testing**
   - [ ] Unit tests for all components
   - [ ] Integration tests for multi-agent flows
   - [ ] Performance testing (parallel execution)
   - [ ] Edge case handling

10. **Documentation & Examples**
    - [ ] API documentation
    - [ ] User guide for multi-agent features
    - [ ] Example tasks and use cases
    - [ ] Configuration guide

## Key Design Decisions

### 1. When to Delegate?

**Auto-delegation triggers**:
- Query mentions "multiple" tasks
- Query has > 3 distinct action verbs
- Estimated tokens > 50K
- Query requires > 2 different skill domains

**User controls**:
- `/delegate <task>` - Force delegation
- `/nodelegete` - Disable auto-delegation for session
- Config: `agents.multi_agent.auto_delegate: true|false`

### 2. Resource Limits

**Per sub-agent**:
- Max iterations: 20 (vs 50 for main)
- Max execution time: 5 minutes
- Max context: 32K tokens
- Max file operations: 100

**System-wide**:
- Max concurrent sub-agents: 5
- Total memory budget: 500MB
- Shared tool rate limits

### 3. Failure Handling

**Sub-agent failure modes**:
1. **Timeout**: Return partial results, mark incomplete
2. **Error**: Retry once, then escalate to main agent
3. **Stuck Loop**: Interrupt after max iterations
4. **Resource Exhaustion**: Save state, request user guidance

**Rollback strategy**:
- Track file changes per sub-agent
- Maintain change log
- Provide rollback option on failure

### 4. Security & Isolation

**Sandboxing**:
- Sub-agents can only access designated directories
- No cross-agent file access
- Separate environment variables
- Limited network access (if configured)

**Permission model**:
- Sub-agents inherit main agent permissions
- Can be restricted via config
- Dangerous operations require confirmation

## Configuration Schema

```yaml
# ~/.dominusprime/config.yaml

agents:
  multi_agent:
    enabled: true
    auto_delegate: true
    
    complexity_threshold: "moderate"  # simple|moderate|complex
    
    pool:
      max_concurrent: 5
      agent_timeout: 300  # seconds
      cleanup_interval: 60  # seconds
    
    execution:
      parallel_enabled: true
      max_parallel_tasks: 3
      sequential_timeout_multiplier: 2.0
    
    resources:
      max_iterations_per_agent: 20
      max_context_tokens: 32768
      max_file_operations: 100
      memory_limit_mb: 500
    
    communication:
      message_queue_size: 1000
      progress_update_interval: 10  # seconds
    
    security:
      sandbox_enabled: true
      allowed_directories:
        - "~/.dominusprime/workspace"
      require_confirmation_for:
        - "delete_file"
        - "execute_shell"
```

## Example Usage

### User Query
```
"Research the top 3 Python web frameworks, create a comparison table, 
and write a recommendation report with code examples for each."
```

### System Behavior

1. **Complexity Analysis**
   - Detected: 3 distinct objectives
   - Complexity: Complex
   - Recommendation: Delegate

2. **Task Decomposition**
   ```
   SubTask 1: Research Python web frameworks
   - Tools: web_search, browser_use
   - Output: List of top 3 frameworks with key facts
   
   SubTask 2: Create comparison table  
   - Dependency: SubTask 1
   - Tools: write_file
   - Output: markdown table file
   
   SubTask 3: Write recommendation report
   - Dependency: SubTask 1, 2
   - Tools: write_file, code_generation
   - Output: report.md with code examples
   ```

3. **Execution**
   ```
   [Main Agent] Spawning sub-agents...
   [SubAgent-1] Researching frameworks...
   [SubAgent-1] Found: Django, Flask, FastAPI
   [SubAgent-1] ✓ Complete
   
   [SubAgent-2] Creating comparison table...
   [SubAgent-2] ✓ Table saved to comparison.md
   
   [SubAgent-3] Writing recommendation report...
   [SubAgent-3] ✓ Report saved to recommendation.md
   
   [Main Agent] All tasks complete!
   ```

4. **Response to User**
   ```
   I've completed your multi-part task:
   
   1. ✓ Researched top 3 Python web frameworks
   2. ✓ Created comparison table (see comparison.md)
   3. ✓ Wrote recommendation report (see recommendation.md)
   
   Summary:
   - Django: Best for large-scale applications
   - Flask: Best for microservices and flexibility
   - FastAPI: Best for modern APIs with async support
   
   I recommend FastAPI for new projects requiring high performance 
   and automatic API documentation.
   
   Files created:
   - comparison.md (framework comparison table)
   - recommendation.md (detailed report with examples)
   ```

## Success Metrics

1. **Performance**
   - Parallel execution reduces total time by 40%+
   - Delegation overhead < 2 seconds
   - Sub-agent spawn time < 500ms

2. **Accuracy**
   - 90%+ correct task decomposition
   - 95%+ successful sub-task completion
   - 98%+ correct result aggregation

3. **User Experience**
   - Clear progress updates every 10s
   - Understandable error messages
   - Intuitive delegation controls

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Incorrect task decomposition | High | LLM validation + user confirmation for complex tasks |
| Sub-agent stuck in loop | Medium | Timeout + max iterations + progress monitoring |
| Memory explosion with many agents | High | Agent pool limits + garbage collection |
| Conflicting file operations | Medium | File locking + operation sequencing |
| Cost explosion (API calls) | High | Token budgets + cost tracking + warnings |

## Future Enhancements

1. **Adaptive Learning**
   - Learn optimal task decomposition from past executions
   - Improve complexity scoring over time
   - Suggest delegation for similar tasks

2. **Agent Specialization**
   - Pre-configured agent templates (researcher, writer, coder)
   - Custom skill combinations
   - Performance-based agent selection

3. **Hierarchical Delegation**
   - Sub-agents can spawn their own sub-agents
   - Multi-level task trees
   - Automatic coordination across levels

4. **Collaborative Agents**
   - Agents can share discoveries in real-time
   - Consensus building for decisions
   - Peer review between agents

## Implementation Notes

- Built on AgentScope's existing agent infrastructure
- Maintains backward compatibility (single-agent mode default)
- Extensible architecture for future agent types
- Configuration-driven for easy customization
- Comprehensive logging for debugging and optimization

---

**Status**: Architecture Design Complete
**Next Step**: Begin Phase 1 implementation
**Target**: DominusPrime v0.9.3 feature release
