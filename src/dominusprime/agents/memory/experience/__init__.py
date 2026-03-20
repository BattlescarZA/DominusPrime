# -*- coding: utf-8 -*-
"""Experience distillation and skill extraction module.

Automatically learns from conversations and generates reusable skills.
"""

from .base import ExperienceType, LearningMoment, Pattern
from .system import ExperienceSystem

__all__ = [
    "ExperienceType",
    "LearningMoment",
    "Pattern",
    "ExperienceSystem",
]
