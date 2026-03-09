# -*- coding: utf-8 -*-
"""Task Decomposer for breaking down complex queries into subtasks."""

import json
import re
from typing import Any, List, Optional

from agentscope.message import Msg
from agentscope.models import ModelWrapperBase

from .complexity_analyzer import TaskComplexityAnalyzer
from .models import ExecutionMode, SubTask, TaskComplexity


class TaskDecomposer:
    """Decomposes complex user queries into manageable subtasks using LLM.
    
    This component analyzes user intent and breaks down complex requests into
    structured subtasks with dependencies, tool requirements, and execution modes.
    """

    # Domain to tool/skill mapping
    DOMAIN_TOOLS = {
        "web": ["web_search", "web_browser", "http_request"],
        "file": ["read_file", "write_file", "list_directory"],
        "data": ["python_execute", "data_analysis"],
        "code": ["code_search", "code_edit", "git_operations"],
        "research": ["web_search", "summarize", "knowledge_base"],
        "writing": ["text_generation", "markdown_editor"],
        "system": ["shell_execute", "process_manager"],
        "communication": ["email", "slack", "notification"],
    }

    def __init__(
        self,
        model: ModelWrapperBase,
        complexity_analyzer: Optional[TaskComplexityAnalyzer] = None,
    ):
        """Initialize the TaskDecomposer.
        
        Args:
            model: LLM model wrapper for task analysis
            complexity_analyzer: Optional complexity analyzer instance
        """
        self.model = model
        self.complexity_analyzer = complexity_analyzer or TaskComplexityAnalyzer()

    async def decompose(
        self,
        query: str,
        context: Optional[List[Msg]] = None,
        max_subtasks: int = 10,
    ) -> List[SubTask]:
        """Decompose a complex query into subtasks.
        
        Args:
            query: User query to decompose
            context: Optional conversation context
            max_subtasks: Maximum number of subtasks to generate
            
        Returns:
            List of SubTask objects with dependencies and configurations
        """
        # First analyze complexity
        complexity = self.complexity_analyzer.analyze(query, context)
        
        if complexity == TaskComplexity.SIMPLE:
            # Don't decompose simple tasks
            return [
                SubTask(
                    id="task_0",
                    description=query,
                    estimated_complexity=complexity,
                    execution_mode=ExecutionMode.SEQUENTIAL,
                )
            ]
        
        # Build LLM prompt for decomposition
        decomposition_prompt = self._build_decomposition_prompt(
            query, complexity, max_subtasks, context
        )
        
        # Get LLM response
        response = await self._query_llm(decomposition_prompt)
        
        # Parse response into subtasks
        subtasks = self._parse_decomposition(response, query)
        
        # Validate and enrich subtasks
        subtasks = self._validate_subtasks(subtasks)
        subtasks = self._enrich_with_tools(subtasks)
        subtasks = self._determine_execution_modes(subtasks)
        
        return subtasks

    def _build_decomposition_prompt(
        self,
        query: str,
        complexity: TaskComplexity,
        max_subtasks: int,
        context: Optional[List[Msg]] = None,
    ) -> str:
        """Build the LLM prompt for task decomposition."""
        context_str = ""
        if context:
            recent_context = context[-3:]  # Last 3 messages
            context_str = "\n\nRecent Conversation Context:\n"
            for msg in recent_context:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_str += f"- {role}: {content}\n"
        
        prompt = f"""You are an expert task decomposition system. Your job is to break down complex user requests into clear, actionable subtasks.

User Request: {query}

Task Complexity: {complexity.value}
Maximum Subtasks: {max_subtasks}
{context_str}

Break this request down into subtasks. For each subtask, provide:
1. A clear, actionable description
2. Dependencies (which subtasks must complete first)
3. Required skills/domains (e.g., web, file, data, code, research, writing, system)
4. Estimated timeout in seconds (default 300)

Output your response in JSON format:
{{
  "subtasks": [
    {{
      "id": "task_1",
      "description": "Clear description of what needs to be done",
      "dependencies": [],
      "required_skills": ["web", "research"],
      "timeout": 300,
      "context": "Any additional context needed for this subtask"
    }},
    {{
      "id": "task_2",
      "description": "Another subtask",
      "dependencies": ["task_1"],
      "required_skills": ["data"],
      "timeout": 600,
      "context": "Additional context"
    }}
  ],
  "execution_strategy": "sequential|parallel|hybrid",
  "reasoning": "Brief explanation of the decomposition strategy"
}}

Guidelines:
- Create atomic, focused subtasks
- Identify true dependencies (task B needs output from task A)
- Use sequential execution when tasks must run in order
- Use parallel execution when tasks are independent
- Use hybrid for mix of sequential and parallel tasks
- Keep descriptions clear and actionable
- Assign realistic timeouts based on task complexity

Respond ONLY with valid JSON."""

        return prompt

    async def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the decomposition prompt.
        
        Args:
            prompt: The decomposition prompt
            
        Returns:
            LLM response text
        """
        # Create message for LLM
        msg = Msg(name="system", role="system", content=prompt)
        
        # Query model
        response = self.model(msg)
        
        # Extract content from response
        if isinstance(response, Msg):
            return response.content
        elif isinstance(response, dict) and "content" in response:
            return response["content"]
        else:
            return str(response)

    def _parse_decomposition(self, response: str, original_query: str) -> List[SubTask]:
        """Parse LLM response into SubTask objects.
        
        Args:
            response: LLM response text
            original_query: Original user query for fallback
            
        Returns:
            List of SubTask objects
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse JSON
            data = json.loads(json_str)
            subtasks_data = data.get("subtasks", [])
            
            if not subtasks_data:
                raise ValueError("No subtasks found in response")
            
            # Convert to SubTask objects
            subtasks = []
            for task_data in subtasks_data:
                subtask = SubTask(
                    id=task_data.get("id", f"task_{len(subtasks)}"),
                    description=task_data.get("description", ""),
                    dependencies=task_data.get("dependencies", []),
                    required_skills=task_data.get("required_skills", []),
                    timeout=task_data.get("timeout", 300),
                    context=task_data.get("context"),
                )
                subtasks.append(subtask)
            
            return subtasks
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback: create single task from original query
            print(f"Failed to parse LLM decomposition: {e}")
            return [
                SubTask(
                    id="task_0",
                    description=original_query,
                    estimated_complexity=TaskComplexity.MODERATE,
                )
            ]

    def _validate_subtasks(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Validate and fix subtask configurations.
        
        Args:
            subtasks: List of subtasks to validate
            
        Returns:
            Validated subtasks
        """
        if not subtasks:
            return subtasks
        
        # Ensure unique IDs
        seen_ids = set()
        for i, task in enumerate(subtasks):
            if not task.id or task.id in seen_ids:
                task.id = f"task_{i}"
            seen_ids.add(task.id)
        
        # Validate dependencies exist
        valid_ids = {task.id for task in subtasks}
        for task in subtasks:
            task.dependencies = [
                dep for dep in task.dependencies if dep in valid_ids
            ]
        
        # Check for circular dependencies
        if self._has_circular_dependencies(subtasks):
            print("Warning: Circular dependencies detected, removing some dependencies")
            subtasks = self._remove_circular_dependencies(subtasks)
        
        # Ensure descriptions are not empty
        for task in subtasks:
            if not task.description or not task.description.strip():
                task.description = f"Execute task {task.id}"
        
        return subtasks

    def _has_circular_dependencies(self, subtasks: List[SubTask]) -> bool:
        """Check if there are circular dependencies.
        
        Args:
            subtasks: List of subtasks to check
            
        Returns:
            True if circular dependencies exist
        """
        # Build dependency graph
        graph = {task.id: task.dependencies for task in subtasks}
        
        # Check each node for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False

    def _remove_circular_dependencies(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Remove circular dependencies from subtasks.
        
        Args:
            subtasks: List of subtasks with circular dependencies
            
        Returns:
            Subtasks with circular dependencies removed
        """
        # Simple strategy: remove dependencies that create cycles
        graph = {task.id: set(task.dependencies) for task in subtasks}
        
        for task in subtasks:
            for dep in list(task.dependencies):
                # Temporarily remove dependency
                if dep in graph[task.id]:
                    graph[task.id].remove(dep)
                    
                    # Check if removing this dependency fixes cycles
                    temp_subtasks = [
                        SubTask(
                            id=t.id,
                            description=t.description,
                            dependencies=list(graph[t.id]),
                        )
                        for t in subtasks
                    ]
                    
                    if not self._has_circular_dependencies(temp_subtasks):
                        # Keep this dependency removed
                        task.dependencies.remove(dep)
                    else:
                        # Restore dependency
                        graph[task.id].add(dep)
        
        return subtasks

    def _enrich_with_tools(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Enrich subtasks with required tools based on skills.
        
        Args:
            subtasks: List of subtasks to enrich
            
        Returns:
            Subtasks with tools assigned
        """
        for task in subtasks:
            tools = set()
            for skill in task.required_skills:
                skill_lower = skill.lower()
                if skill_lower in self.DOMAIN_TOOLS:
                    tools.update(self.DOMAIN_TOOLS[skill_lower])
            
            task.required_tools = list(tools)
        
        return subtasks

    def _determine_execution_modes(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Determine execution mode for each subtask.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            Subtasks with execution modes set
        """
        # Build dependency graph
        has_dependencies = {
            task.id: len(task.dependencies) > 0 for task in subtasks
        }
        
        # Tasks with no dependencies can run in parallel
        # Tasks with dependencies run sequentially
        for task in subtasks:
            if has_dependencies[task.id]:
                task.execution_mode = ExecutionMode.SEQUENTIAL
            else:
                # Check if other tasks depend on this one
                is_dependency = any(
                    task.id in t.dependencies for t in subtasks if t.id != task.id
                )
                if is_dependency:
                    task.execution_mode = ExecutionMode.SEQUENTIAL
                else:
                    task.execution_mode = ExecutionMode.PARALLEL
        
        return subtasks

    def estimate_total_time(self, subtasks: List[SubTask]) -> float:
        """Estimate total execution time for subtasks.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            Estimated total time in seconds
        """
        if not subtasks:
            return 0.0
        
        # Build dependency levels
        levels = self._build_dependency_levels(subtasks)
        
        # Calculate time per level (parallel tasks in same level)
        total_time = 0.0
        for level_tasks in levels:
            # Max time in this level (tasks run in parallel)
            level_time = max(task.timeout for task in level_tasks)
            total_time += level_time
        
        return total_time

    def _build_dependency_levels(
        self, subtasks: List[SubTask]
    ) -> List[List[SubTask]]:
        """Build dependency levels for subtasks.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            List of levels, each containing tasks that can run in parallel
        """
        # Create task lookup
        task_map = {task.id: task for task in subtasks}
        
        # Calculate level for each task
        levels_dict: dict[str, int] = {}
        
        def calculate_level(task_id: str) -> int:
            if task_id in levels_dict:
                return levels_dict[task_id]
            
            task = task_map.get(task_id)
            if not task or not task.dependencies:
                levels_dict[task_id] = 0
                return 0
            
            # Level is max(dependency levels) + 1
            max_dep_level = max(
                calculate_level(dep) for dep in task.dependencies
            )
            levels_dict[task_id] = max_dep_level + 1
            return max_dep_level + 1
        
        # Calculate levels for all tasks
        for task in subtasks:
            calculate_level(task.id)
        
        # Group tasks by level
        max_level = max(levels_dict.values()) if levels_dict else 0
        levels = [[] for _ in range(max_level + 1)]
        
        for task in subtasks:
            level = levels_dict.get(task.id, 0)
            levels[level].append(task)
        
        return levels
