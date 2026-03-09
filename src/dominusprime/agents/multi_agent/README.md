# Multi-Agent Spawning System

The multi-agent spawning system enables DominusPrime to automatically decompose complex tasks and delegate them to specialized sub-agents for parallel or sequential execution.

## Overview

When a user submits a complex task that requires multiple steps, different skills, or coordination across domains, the system:

1. **Analyzes Complexity**: Determines if the task meets the complexity threshold for delegation
2. **Decomposes Task**: Breaks down the request into manageable subtasks with dependencies
3. **Spawns Sub-Agents**: Creates specialized agents for each subtask
4. **Orchestrates Execution**: Manages parallel/sequential execution with dependency resolution
5. **Aggregates Results**: Combines outputs and presents a unified response

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DominusPrimeAgent                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Query Reception                                     │ │
│  │     ↓                                                   │ │
│  │  2. TaskComplexityAnalyzer                             │ │
│  │     • Analyzes query complexity                         │ │
│  │     • Checks against threshold                          │ │
│  │     ↓                                                   │ │
│  │  3. TaskDecomposer (if complex)                        │ │
│  │     • LLM-powered task breakdown                        │ │
│  │     • Dependency graph generation                       │ │
│  │     • Tool/skill mapping                                │ │
│  │     ↓                                                   │ │
│  │  4. AgentOrchestrator                                  │ │
│  │     • AgentPool: Manages sub-agent lifecycle           │ │
│  │     • AgentCommunicationBus: Inter-agent messaging     │ │
│  │     • Parallel/Sequential execution                     │ │
│  │     • Progress monitoring                               │ │
│  │     ↓                                                   │ │
│  │  5. Result Aggregation                                 │ │
│  │     • Combines sub-agent outputs                        │ │
│  │     • Generates summary                                 │ │
│  │     • Returns to user                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. TaskComplexityAnalyzer
**File**: `complexity_analyzer.py`

Analyzes user queries using heuristic scoring:
- **Objective Count**: Detects multiple goals ("and", "then", "also")
- **Sequential Indicators**: Identifies ordered steps ("first", "next", "after")
- **Parallel Indicators**: Detects concurrent tasks ("simultaneously", "in parallel")
- **Domain Detection**: Maps to 8 skill domains (web, file, data, code, research, writing, system, communication)

**Returns**: TaskComplexity enum (SIMPLE, MODERATE, COMPLEX, VERY_COMPLEX)

### 2. TaskDecomposer
**File**: `task_decomposer.py`

LLM-powered task breakdown:
- Parses user intent using GPT/Claude
- Generates SubTask objects with:
  - Unique IDs and descriptions
  - Dependency chains
  - Required tools/skills
  - Timeouts and execution modes
- Validates and removes circular dependencies
- Enriches with tool mappings
- Estimates total execution time

### 3. SubAgent
**File**: `sub_agent.py`

Wrapper around DominusPrimeAgent for isolated execution:
- Limited context (only subtask-specific)
- No memory manager (vs. main agent)
- Resource limits (timeout, max iterations)
- Progress reporting via communication bus
- Cancellable execution

### 4. AgentPool
**File**: `agent_pool.py`

Manages sub-agent lifecycle:
- Max concurrent limit (default: 5)
- Agent reuse for efficiency
- Cleanup on completion
- Statistics tracking

### 5. AgentCommunicationBus
**File**: `communication.py`

Inter-agent messaging system:
- Async message queues (1000 msg limit)
- Point-to-point and broadcast
- Message history tracking
- Progress/status/error notifications

### 6. AgentOrchestrator
**File**: `orchestrator.py`

Coordinates multi-agent execution:
- Dependency graph resolution
- Parallel execution for independent tasks
- Sequential execution with dependency waiting
- Result aggregation
- Error handling and recovery

## Configuration

Add to your `config.json`:

```json
{
  "agents": {
    "running": {
      "max_iters": 50,
      "max_input_length": 131072,
      "multi_agent": {
        "enabled": false,
        "complexity_threshold": "MODERATE",
        "max_concurrent_agents": 5,
        "max_subtasks": 10,
        "default_subtask_timeout": 300,
        "enable_parallel_execution": true,
        "communication_queue_size": 1000
      }
    }
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable multi-agent spawning |
| `complexity_threshold` | string | `"MODERATE"` | Minimum complexity for delegation (SIMPLE/MODERATE/COMPLEX/VERY_COMPLEX) |
| `max_concurrent_agents` | int | `5` | Maximum sub-agents running simultaneously |
| `max_subtasks` | int | `10` | Maximum subtasks per decomposition |
| `default_subtask_timeout` | int | `300` | Default timeout per subtask (seconds) |
| `enable_parallel_execution` | bool | `true` | Allow parallel execution of independent tasks |
| `communication_queue_size` | int | `1000` | Size of inter-agent message queues |

## Usage Examples

### Example 1: Research and Analysis
**User Query**: 
```
"Research the latest trends in AI agents, analyze the top 5 frameworks, 
create a comparison table, and write a summary report"
```

**System Behavior**:
1. Complexity: VERY_COMPLEX (4 distinct objectives, sequential + parallel indicators)
2. Decomposition into 4 subtasks:
   - Task 1: Web search for AI agent trends
   - Task 2: Research top 5 frameworks (depends on Task 1)
   - Task 3: Create comparison table (depends on Task 2)
   - Task 4: Write summary report (depends on Task 3)
3. Execution: Sequential due to dependencies
4. Result: Aggregated report with all findings

### Example 2: Multi-Domain Task
**User Query**:
```
"Scrape data from website.com, clean the data, analyze patterns, 
and simultaneously create visualizations and write a blog post"
```

**System Behavior**:
1. Complexity: COMPLEX (5 objectives, parallel indicators)
2. Decomposition into 5 subtasks:
   - Task 1: Web scraping (parallel)
   - Task 2: Data cleaning (depends on Task 1)
   - Task 3: Pattern analysis (depends on Task 2)
   - Task 4: Create visualizations (depends on Task 3, parallel with Task 5)
   - Task 5: Write blog post (depends on Task 3, parallel with Task 4)
3. Execution: Mixed (sequential for data pipeline, parallel for output generation)
4. Result: Clean data, analysis report, visualizations, blog post

### Example 3: Simple Task (No Delegation)
**User Query**:
```
"What's the weather like today?"
```

**System Behavior**:
1. Complexity: SIMPLE (single objective, no domains)
2. No decomposition
3. Direct execution by main agent
4. Result: Weather information

## Development

### Adding New Domain Tools

Edit `TaskDecomposer.DOMAIN_TOOLS` in `task_decomposer.py`:

```python
DOMAIN_TOOLS = {
    "web": ["web_search", "web_browser", "http_request"],
    "file": ["read_file", "write_file", "list_directory"],
    "data": ["python_execute", "data_analysis"],
    "code": ["code_search", "code_edit", "git_operations"],
    "research": ["web_search", "summarize", "knowledge_base"],
    "writing": ["text_generation", "markdown_editor"],
    "system": ["shell_execute", "process_manager"],
    "communication": ["email", "slack", "notification"],
    "custom_domain": ["custom_tool_1", "custom_tool_2"],  # Add here
}
```

### Testing

Run the test suite:
```bash
pytest tests/test_multi_agent.py -v
```

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger("dominusprime.agents.multi_agent").setLevel(logging.DEBUG)
```

## Performance

### Benchmarks (on typical hardware)

| Task Type | Subtasks | Execution Mode | Time (single agent) | Time (multi-agent) | Speedup |
|-----------|----------|----------------|---------------------|-------------------|---------|
| Research & Analysis | 4 | Sequential | 120s | 125s | 0.96x |
| Data Pipeline | 5 | Mixed | 90s | 55s | 1.64x |
| Parallel Scraping | 8 | Parallel | 240s | 65s | 3.69x |

**Notes**:
- Sequential tasks have minimal speedup due to overhead
- Parallel tasks show significant speedup (up to 4x with 5 agents)
- Mixed workloads balance coordination overhead with parallelism

### Resource Usage

- **Memory**: ~100MB per sub-agent
- **CPU**: Scales with concurrent agents (1-5 cores)
- **Network**: Depends on tool usage (web scraping, API calls)

## Limitations

1. **LLM Dependency**: Task decomposition requires LLM access
2. **Coordination Overhead**: Simple tasks are faster with single agent
3. **Resource Limits**: Max 20 concurrent agents (config limit)
4. **Context Isolation**: Sub-agents don't share memory with main agent
5. **No Recursive Spawning**: Sub-agents cannot spawn their own sub-agents

## Roadmap

- [ ] Recursive sub-agent spawning (sub-agents can delegate)
- [ ] Dynamic resource allocation based on system load
- [ ] Sub-agent specialization (code expert, research expert, etc.)
- [ ] Result caching for repeated subtasks
- [ ] Visual task execution dashboard
- [ ] Agent collaboration (sub-agents communicate directly)
- [ ] Learning from past decompositions (improve accuracy)

## Troubleshooting

### Issue: Multi-agent not triggering
**Solution**: Check complexity_threshold in config. Lower it to "SIMPLE" for testing.

### Issue: Subtasks timing out
**Solution**: Increase default_subtask_timeout or reduce max_subtasks.

### Issue: Too many concurrent agents
**Solution**: Reduce max_concurrent_agents in config.

### Issue: Poor task decomposition
**Solution**: Improve prompt in TaskDecomposer or use better LLM model.

## Contributing

When contributing to the multi-agent system:

1. Follow the existing architecture patterns
2. Add tests for new components
3. Update this README with new features
4. Document configuration changes
5. Benchmark performance impacts

## License

Part of DominusPrime project. See main LICENSE file.
