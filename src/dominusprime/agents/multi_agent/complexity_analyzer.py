# -*- coding: utf-8 -*-
"""Task complexity analysis for determining delegation needs."""

import logging
import re
from typing import List, Optional

from agentscope.message import Msg

from .models import TaskComplexity

logger = logging.getLogger(__name__)


class TaskComplexityAnalyzer:
    """Analyzes user queries to determine if task decomposition is beneficial.

    Detects:
    - Multiple distinct objectives
    - Sequential dependencies
    - Different skill domains
    - Estimated execution complexity
    """

    # Keywords indicating multiple objectives
    MULTIPLE_OBJECTIVES = [
        "and",
        "also",
        "additionally",
        "furthermore",
        "moreover",
        "as well as",
        "along with",
    ]

    # Keywords indicating sequential steps
    SEQUENTIAL_INDICATORS = [
        "first",
        "then",
        "next",
        "after",
        "finally",
        "subsequently",
        "before",
        "once",
        "when done",
    ]

    # Keywords indicating parallel tasks
    PARALLEL_INDICATORS = [
        "simultaneously",
        "at the same time",
        "in parallel",
        "concurrently",
        "while",
    ]

    # Domain-specific keywords
    DOMAIN_KEYWORDS = {
        "web": ["search", "browse", "scrape", "fetch", "website", "url", "download"],
        "file": ["read", "write", "edit", "file", "document", "save", "create"],
        "data": ["analyze", "process", "calculate", "statistics", "data", "csv"],
        "code": ["code", "script", "program", "function", "debug", "test"],
        "research": ["research", "investigate", "find", "discover", "learn"],
        "writing": ["write", "compose", "draft", "report", "essay", "article"],
    }

    def __init__(self, threshold: TaskComplexity = TaskComplexity.MODERATE):
        """Initialize analyzer.

        Args:
            threshold: Minimum complexity to trigger delegation
        """
        self.threshold = threshold

    def analyze(
        self,
        query: str,
        context: Optional[List[Msg]] = None,
    ) -> TaskComplexity:
        """Analyze task complexity.

        Args:
            query: User query to analyze
            context: Previous conversation messages

        Returns:
            TaskComplexity level
        """
        query_lower = query.lower()

        # Calculate various complexity indicators
        objective_count = self._count_objectives(query_lower)
        has_sequential = self._has_sequential_steps(query_lower)
        has_parallel = self._has_parallel_tasks(query_lower)
        domain_count = self._count_domains(query_lower)
        query_length = len(query.split())

        # Score complexity
        complexity_score = 0

        # Multiple objectives add to complexity
        if objective_count > 2:
            complexity_score += 2
        elif objective_count > 1:
            complexity_score += 1

        # Sequential steps indicate complexity
        if has_sequential:
            complexity_score += 1

        # Parallel tasks indicate high complexity
        if has_parallel:
            complexity_score += 2

        # Multiple domains require coordination
        if domain_count > 2:
            complexity_score += 2
        elif domain_count > 1:
            complexity_score += 1

        # Long queries are often complex
        if query_length > 100:
            complexity_score += 2
        elif query_length > 50:
            complexity_score += 1

        # Determine complexity level
        if complexity_score >= 6:
            complexity = TaskComplexity.VERY_COMPLEX
        elif complexity_score >= 4:
            complexity = TaskComplexity.COMPLEX
        elif complexity_score >= 2:
            complexity = TaskComplexity.MODERATE
        else:
            complexity = TaskComplexity.SIMPLE

        logger.info(
            f"Task complexity: {complexity.value} (score: {complexity_score})"
        )
        logger.debug(
            f"Analysis: objectives={objective_count}, "
            f"sequential={has_sequential}, parallel={has_parallel}, "
            f"domains={domain_count}, length={query_length}"
        )

        return complexity

    def should_delegate(self, complexity: TaskComplexity) -> bool:
        """Determine if task should be delegated to sub-agents.

        Args:
            complexity: Task complexity level

        Returns:
            True if task should be delegated
        """
        complexity_order = [
            TaskComplexity.SIMPLE,
            TaskComplexity.MODERATE,
            TaskComplexity.COMPLEX,
            TaskComplexity.VERY_COMPLEX,
        ]

        task_index = complexity_order.index(complexity)
        threshold_index = complexity_order.index(self.threshold)

        return task_index >= threshold_index

    def _count_objectives(self, query: str) -> int:
        """Count distinct objectives in query.

        Args:
            query: Lowercase query string

        Returns:
            Number of distinct objectives
        """
        # Split by common conjunctions
        segments = re.split(r'\band\b|\bthen\b|,', query)

        # Count segments with action verbs
        action_verbs = [
            "create", "make", "write", "read", "analyze", "find",
            "search", "browse", "fetch", "calculate", "process",
            "generate", "build", "design", "implement", "test",
        ]

        objective_count = 0
        for segment in segments:
            if any(verb in segment for verb in action_verbs):
                objective_count += 1

        return max(1, objective_count)

    def _has_sequential_steps(self, query: str) -> bool:
        """Check if query indicates sequential steps.

        Args:
            query: Lowercase query string

        Returns:
            True if sequential indicators found
        """
        return any(indicator in query for indicator in self.SEQUENTIAL_INDICATORS)

    def _has_parallel_tasks(self, query: str) -> bool:
        """Check if query indicates parallel tasks.

        Args:
            query: Lowercase query string

        Returns:
            True if parallel indicators found
        """
        return any(indicator in query for indicator in self.PARALLEL_INDICATORS)

    def _count_domains(self, query: str) -> int:
        """Count different skill domains required.

        Args:
            query: Lowercase query string

        Returns:
            Number of domains detected
        """
        domains_found = set()

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(keyword in query for keyword in keywords):
                domains_found.add(domain)

        return len(domains_found)

    def get_complexity_explanation(
        self,
        query: str,
        complexity: TaskComplexity,
    ) -> str:
        """Generate human-readable explanation of complexity.

        Args:
            query: Original query
            complexity: Determined complexity

        Returns:
            Explanation string
        """
        query_lower = query.lower()

        reasons = []

        objective_count = self._count_objectives(query_lower)
        if objective_count > 1:
            reasons.append(f"{objective_count} distinct objectives")

        if self._has_sequential_steps(query_lower):
            reasons.append("sequential steps required")

        if self._has_parallel_tasks(query_lower):
            reasons.append("parallel execution possible")

        domain_count = self._count_domains(query_lower)
        if domain_count > 1:
            reasons.append(f"{domain_count} different skill domains")

        if len(query.split()) > 50:
            reasons.append("detailed/lengthy request")

        if reasons:
            return (
                f"Task complexity: {complexity.value}. "
                f"Reasons: {', '.join(reasons)}."
            )
        else:
            return f"Task complexity: {complexity.value}. Simple single-step task."
