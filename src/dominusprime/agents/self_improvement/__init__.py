# -*- coding: utf-8 -*-
"""
Self-Improvement System for DominusPrime Agents

This module implements autonomous self-improvement capabilities inspired by
autoresearch (https://github.com/karpathy/autoresearch).

Agents can:
1. Improve individual skills through experimentation
2. Optimize agent-level behavior
3. Meta-improve the improvement process itself
"""

from .config import ImprovementConfig, ImprovementPolicy
from .evaluator import EvaluationResult, TestSuite, Evaluator
from .experiment import Experiment, ExperimentLog
from .skill_improver import SkillSelfImprover
from .agent_improver import AgentSelfImprover

__all__ = [
    "ImprovementConfig",
    "ImprovementPolicy",
    "EvaluationResult",
    "TestSuite",
    "Evaluator",
    "Experiment",
    "ExperimentLog",
    "SkillSelfImprover",
    "AgentSelfImprover",
]
