# -*- coding: utf-8 -*-
"""Agent utilities."""

from .skill_utils import (
    parse_frontmatter,
    skill_matches_platform,
    extract_skill_description,
    extract_skill_conditions,
    validate_skill_name,
    validate_skill_category,
    validate_skill_frontmatter,
    get_disabled_skill_names,
    get_skills_directory,
    iter_skill_files,
    find_skill_by_name,
    build_skill_path,
    get_skill_subdirs,
)
from .skills_index import (
    build_skills_index,
    build_skills_index_compact,
    get_cached_skills_index,
    clear_skills_index_cache,
)
from .context_manager import (
    ContextManager,
    ContextConfig,
    create_context_manager,
    DEFAULT_CONTEXT_LENGTH,
    COMPRESSION_THRESHOLD,
)
from .advanced_cache import (
    LRUCache,
    get_skills_cache,
    get_context_cache,
)
from .trajectory_tracker import (
    ToolCall,
    Trajectory,
    TrajectoryTracker,
)
from .skill_template_generator import (
    SkillTemplateGenerator,
)
from .skill_approval import (
    SkillApprovalWorkflow,
    propose_skill_from_trajectory,
)

__all__ = [
    # Skill utilities
    "parse_frontmatter",
    "skill_matches_platform",
    "extract_skill_description",
    "extract_skill_conditions",
    "validate_skill_name",
    "validate_skill_category",
    "validate_skill_frontmatter",
    "get_disabled_skill_names",
    "get_skills_directory",
    "iter_skill_files",
    "find_skill_by_name",
    "build_skill_path",
    "get_skill_subdirs",
    # Skills index
    "build_skills_index",
    "build_skills_index_compact",
    "get_cached_skills_index",
    "clear_skills_index_cache",
    # Context management
    "ContextManager",
    "ContextConfig",
    "create_context_manager",
    "DEFAULT_CONTEXT_LENGTH",
    "COMPRESSION_THRESHOLD",
    # Advanced caching
    "LRUCache",
    "get_skills_cache",
    "get_context_cache",
    # Auto-generation
    "ToolCall",
    "Trajectory",
    "TrajectoryTracker",
    "SkillTemplateGenerator",
    "SkillApprovalWorkflow",
    "propose_skill_from_trajectory",
]
