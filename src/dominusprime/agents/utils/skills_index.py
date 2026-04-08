# -*- coding: utf-8 -*-
"""
Skills Index Builder - Build summary of available skills for system prompt.

This module creates a concise index of available skills that gets injected into
the agent's system prompt, making skills discoverable and accessible.
"""
import logging
from typing import Dict, List, Optional

from .skill_utils import (
    extract_skill_description,
    get_disabled_skill_names,
    get_skills_directory,
    iter_skill_files,
    parse_frontmatter,
    skill_matches_platform,
)

logger = logging.getLogger(__name__)


def build_skills_index(
    max_skills: int = 50,
    max_desc_length: int = 80,
    include_disabled: bool = False,
) -> str:
    """
    Build a concise skills index for injection into system prompt.
    
    Args:
        max_skills: Maximum number of skills to include
        max_desc_length: Maximum description length per skill
        include_disabled: Include disabled skills
    
    Returns:
        Formatted skills index string, or empty string if no skills
    
    Example output:
        ## Available Skills
        
        Skills are procedural knowledge units you can view, create, and manage.
        Use `await skills(action="list")` to see all, `await skills(action="view", name="skill-name")` to view.
        
        **Development (2)**:
        - `python-debugging`: Debug Python applications using pdb and logging
        - `git-workflow`: Best practices for Git version control
        
        **Research (1)**:
        - `web-research`: Conduct effective web research using browser automation
        
        Use `await skill_manage(action="create", ...)` to create new skills during task execution.
    """
    try:
        skills_dir = get_skills_directory()
        
        # Check if skills directory exists and has skills
        if not skills_dir.exists():
            return ""
        
        disabled_names = get_disabled_skill_names() if not include_disabled else set()
        
        # Build skill index grouped by category
        skills_by_category: Dict[str, List[Dict[str, str]]] = {}
        skill_count = 0
        
        for skill_path in iter_skill_files(skills_dir):
            if skill_count >= max_skills:
                break
            
            skill_dir = skill_path.parent
            
            # Extract category and name from path
            rel_path = skill_dir.relative_to(skills_dir)
            parts = rel_path.parts
            
            if len(parts) == 1:
                category = "General"
                name = parts[0]
            else:
                category = parts[0].replace("-", " ").title()
                name = parts[1]
            
            # Check if disabled
            if name in disabled_names:
                continue
            
            # Parse frontmatter
            try:
                content = skill_path.read_text(encoding="utf-8")
                frontmatter, _ = parse_frontmatter(content)
            except Exception as e:
                logger.debug(f"Failed to parse skill '{name}': {e}")
                continue
            
            # Check platform compatibility
            if not skill_matches_platform(frontmatter):
                continue
            
            # Extract description
            description = extract_skill_description(frontmatter, max_length=max_desc_length)
            if not description:
                description = "No description available"
            
            # Add to category
            if category not in skills_by_category:
                skills_by_category[category] = []
            
            skills_by_category[category].append({
                "name": name,
                "description": description,
            })
            
            skill_count += 1
        
        # If no skills found, return empty string
        if not skills_by_category:
            return ""
        
        # Build formatted output
        lines = [
            "## Available Skills",
            "",
            "Skills are procedural knowledge units you can view, create, and manage.",
            "Use `await skills(action=\"list\")` to see all, `await skills(action=\"view\", name=\"skill-name\")` to view one.",
            "",
        ]
        
        # Add skills grouped by category
        for category in sorted(skills_by_category.keys()):
            skills = skills_by_category[category]
            lines.append(f"**{category} ({len(skills)})**:")
            
            for skill in sorted(skills, key=lambda s: s["name"]):
                lines.append(f"- `{skill['name']}`: {skill['description']}")
            
            lines.append("")
        
        # Add usage hint
        lines.extend([
            "**Managing Skills**:",
            "- Create: `await skill_manage(action=\"create\", name=\"my-skill\", content=\"...\")`",
            "- Search: `await skills(action=\"search\", query=\"debug\")`",
            "- Get categories: `await skills(action=\"categories\")`",
            "",
            "Create new skills during task execution to capture reusable procedures.",
        ])
        
        return "\n".join(lines)
    
    except Exception as e:
        logger.error(f"Failed to build skills index: {e}", exc_info=True)
        return ""


def build_skills_index_compact(max_skills: int = 20) -> str:
    """
    Build an ultra-compact skills index for token-constrained scenarios.
    
    Args:
        max_skills: Maximum number of skills to include
    
    Returns:
        Compact skills index (one line per skill)
    
    Example:
        ## Skills
        python-debugging, web-research, log-analysis, git-workflow
        Use: await skills(action="list|view|search")
    """
    try:
        skills_dir = get_skills_directory()
        
        if not skills_dir.exists():
            return ""
        
        disabled_names = get_disabled_skill_names()
        skill_names = []
        
        for skill_path in iter_skill_files(skills_dir):
            if len(skill_names) >= max_skills:
                break
            
            skill_dir = skill_path.parent
            rel_path = skill_dir.relative_to(skills_dir)
            name = rel_path.parts[-1]
            
            if name in disabled_names:
                continue
            
            # Check platform compatibility
            try:
                content = skill_path.read_text(encoding="utf-8")
                frontmatter, _ = parse_frontmatter(content)
                if not skill_matches_platform(frontmatter):
                    continue
            except Exception:
                continue
            
            skill_names.append(name)
        
        if not skill_names:
            return ""
        
        return (
            "## Skills\n"
            f"{', '.join(sorted(skill_names))}\n"
            "Use: await skills(action=\"list|view|search\") or skill_manage(action=\"create|edit|delete\")"
        )
    
    except Exception as e:
        logger.error(f"Failed to build compact skills index: {e}", exc_info=True)
        return ""


# Cache for skills index to avoid rebuilding on every prompt
_skills_index_cache: Optional[str] = None
_skills_index_cache_compact: Optional[str] = None


def get_cached_skills_index(compact: bool = False) -> str:
    """
    Get cached skills index, building if necessary.
    
    Args:
        compact: Use compact format
    
    Returns:
        Skills index string (cached)
    """
    global _skills_index_cache, _skills_index_cache_compact
    
    if compact:
        if _skills_index_cache_compact is None:
            _skills_index_cache_compact = build_skills_index_compact()
        return _skills_index_cache_compact
    else:
        if _skills_index_cache is None:
            _skills_index_cache = build_skills_index()
        return _skills_index_cache


def clear_skills_index_cache() -> None:
    """Clear the skills index cache to force rebuild."""
    global _skills_index_cache, _skills_index_cache_compact
    _skills_index_cache = None
    _skills_index_cache_compact = None


__all__ = [
    "build_skills_index",
    "build_skills_index_compact",
    "get_cached_skills_index",
    "clear_skills_index_cache",
]
