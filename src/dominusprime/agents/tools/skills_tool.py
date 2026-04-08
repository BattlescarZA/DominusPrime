# -*- coding: utf-8 -*-
"""
Skills Tool - Agent-facing tool for discovering and viewing skills.

This tool allows agents to:
- List all available skills (with filtering)
- View skill content
- Search skills by name, description, or content

Skills are stored in ~/.dominusprime/skills/ with structure:
  category/skill-name/SKILL.md
  category/skill-name/references/
  category/skill-name/templates/
  category/skill-name/scripts/
  category/skill-name/assets/
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.skill_utils import (
    extract_skill_conditions,
    extract_skill_description,
    find_skill_by_name,
    get_disabled_skill_names,
    get_skills_directory,
    iter_skill_files,
    parse_frontmatter,
    skill_matches_platform,
)

logger = logging.getLogger(__name__)


def _get_skill_index(
    include_disabled: bool = False,
    category_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Build index of all skills.
    
    Args:
        include_disabled: Include disabled skills
        category_filter: Filter by category name
    
    Returns:
        List of skill metadata dicts with keys:
        - name: skill name
        - category: category name or None
        - description: truncated description
        - platforms: list of compatible platforms
        - required_tools: list of required tools
        - required_toolsets: list of required toolsets
        - path: absolute path to skill directory
        - disabled: whether skill is disabled
    """
    skills_dir = get_skills_directory()
    disabled_names = get_disabled_skill_names()
    
    index = []
    
    for skill_path in iter_skill_files(skills_dir):
        skill_dir = skill_path.parent
        
        # Extract category and name from path
        rel_path = skill_dir.relative_to(skills_dir)
        parts = rel_path.parts
        
        if len(parts) == 1:
            category = None
            name = parts[0]
        else:
            category = parts[0]
            name = parts[1]
        
        # Apply category filter
        if category_filter and category != category_filter:
            continue
        
        # Check if disabled
        is_disabled = name in disabled_names
        if is_disabled and not include_disabled:
            continue
        
        # Parse frontmatter
        try:
            content = skill_path.read_text(encoding="utf-8")
            frontmatter, _ = parse_frontmatter(content)
        except Exception as e:
            logger.warning(f"Failed to parse skill '{name}': {e}")
            continue
        
        # Extract metadata
        description = extract_skill_description(frontmatter)
        platforms = frontmatter.get("platforms", [])
        conditions = extract_skill_conditions(frontmatter)
        
        index.append({
            "name": name,
            "category": category,
            "description": description,
            "platforms": platforms,
            "required_tools": conditions.get("required_tools", []),
            "required_toolsets": conditions.get("required_toolsets", []),
            "path": str(skill_dir),
            "disabled": is_disabled,
        })
    
    # Sort by category, then name
    index.sort(key=lambda x: (x["category"] or "", x["name"]))
    
    return index


def _list_skills(
    category: Optional[str] = None,
    include_disabled: bool = False,
    platform_filter: bool = True,
) -> Dict[str, Any]:
    """
    List all available skills.
    
    Args:
        category: Filter by category
        include_disabled: Include disabled skills
        platform_filter: Only show platform-compatible skills
    
    Returns:
        {"success": bool, "skills": List[Dict], "count": int}
    """
    try:
        index = _get_skill_index(include_disabled, category)
        
        # Apply platform filter
        if platform_filter:
            index = [
                skill for skill in index
                if not skill["platforms"] or skill_matches_platform(
                    {"platforms": skill["platforms"]}
                )
            ]
        
        return {
            "success": True,
            "skills": index,
            "count": len(index),
        }
    
    except Exception as e:
        logger.error(f"Failed to list skills: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to list skills: {e}",
            "skills": [],
            "count": 0,
        }


def _view_skill(
    name: str,
    include_supporting_files: bool = False,
) -> Dict[str, Any]:
    """
    View skill content.
    
    Args:
        name: Skill name
        include_supporting_files: Include references, templates, etc.
    
    Returns:
        {
            "success": bool,
            "name": str,
            "category": str | None,
            "content": str,  # SKILL.md content
            "frontmatter": Dict,
            "supporting_files": List[Dict] | None,  # if include_supporting_files
        }
    """
    # Find skill
    skill_path = find_skill_by_name(name)
    if not skill_path:
        return {"success": False, "message": f"Skill '{name}' not found"}
    
    # Extract category
    skills_dir = get_skills_directory()
    rel_path = skill_path.relative_to(skills_dir)
    parts = rel_path.parts
    category = parts[0] if len(parts) > 1 else None
    
    # Read SKILL.md
    skill_file = skill_path / "SKILL.md"
    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to read SKILL.md: {e}",
        }
    
    # Parse frontmatter
    try:
        frontmatter, body = parse_frontmatter(content)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to parse frontmatter: {e}",
        }
    
    result = {
        "success": True,
        "name": name,
        "category": category,
        "content": content,
        "frontmatter": frontmatter,
        "body": body,
    }
    
    # Include supporting files if requested
    if include_supporting_files:
        supporting_files = []
        
        for subdir in ["references", "templates", "scripts", "assets"]:
            subdir_path = skill_path / subdir
            if not subdir_path.exists():
                continue
            
            for file_path in subdir_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                rel_file_path = file_path.relative_to(skill_path)
                
                # Read file content (skip large files)
                if file_path.stat().st_size > 100_000:  # 100KB limit
                    file_content = "<file too large to display>"
                else:
                    try:
                        file_content = file_path.read_text(encoding="utf-8")
                    except (UnicodeDecodeError, PermissionError):
                        file_content = "<binary file>"
                
                supporting_files.append({
                    "path": str(rel_file_path),
                    "size": file_path.stat().st_size,
                    "content": file_content,
                })
        
        result["supporting_files"] = supporting_files
    
    return result


def _search_skills(
    query: str,
    search_content: bool = False,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search skills by name, description, or content.
    
    Args:
        query: Search query (case-insensitive substring match)
        search_content: Also search in skill body content
        category: Filter by category
    
    Returns:
        {
            "success": bool,
            "results": List[Dict],
            "count": int,
        }
    """
    try:
        index = _get_skill_index(include_disabled=False, category_filter=category)
        
        query_lower = query.lower()
        results = []
        
        for skill in index:
            name = skill["name"]
            description = skill["description"]
            
            # Search in name and description
            if query_lower in name.lower() or query_lower in description.lower():
                results.append({
                    **skill,
                    "match_type": "metadata",
                })
                continue
            
            # Search in content if requested
            if search_content:
                skill_path = find_skill_by_name(name)
                if not skill_path:
                    continue
                
                skill_file = skill_path / "SKILL.md"
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    if query_lower in content.lower():
                        results.append({
                            **skill,
                            "match_type": "content",
                        })
                except Exception as e:
                    logger.warning(f"Failed to search skill '{name}': {e}")
                    continue
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
        }
    
    except Exception as e:
        logger.error(f"Failed to search skills: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to search skills: {e}",
            "results": [],
            "count": 0,
        }


def _get_categories() -> Dict[str, Any]:
    """
    Get list of all skill categories.
    
    Returns:
        {
            "success": bool,
            "categories": List[str],
            "count": int,
        }
    """
    try:
        skills_dir = get_skills_directory()
        categories = set()
        
        for skill_path in iter_skill_files(skills_dir):
            skill_dir = skill_path.parent
            rel_path = skill_dir.relative_to(skills_dir)
            parts = rel_path.parts
            
            if len(parts) > 1:
                categories.add(parts[0])
        
        categories_list = sorted(categories)
        
        return {
            "success": True,
            "categories": categories_list,
            "count": len(categories_list),
        }
    
    except Exception as e:
        logger.error(f"Failed to get categories: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to get categories: {e}",
            "categories": [],
            "count": 0,
        }


# ============================================================================
# Main Tool Function
# ============================================================================

async def skills(
    action: str,
    name: Optional[str] = None,
    query: Optional[str] = None,
    category: Optional[str] = None,
    include_disabled: bool = False,
    include_supporting_files: bool = False,
    search_content: bool = False,
    platform_filter: bool = True,
) -> str:
    """
    Discover and view skills.
    
    Args:
        action: Action to perform (list|view|search|categories)
        name: Skill name (for 'view' action)
        query: Search query (for 'search' action)
        category: Filter by category (for 'list' and 'search' actions)
        include_disabled: Include disabled skills (for 'list' action)
        include_supporting_files: Include references/templates/etc (for 'view' action)
        search_content: Search in skill body content (for 'search' action)
        platform_filter: Only show platform-compatible skills (for 'list' action)
    
    Returns:
        JSON-formatted result string.
    
    Examples:
        # List all skills
        await skills(action="list")
        
        # List skills in specific category
        await skills(action="list", category="development")
        
        # List all skills including disabled
        await skills(action="list", include_disabled=True)
        
        # View a skill
        await skills(action="view", name="python-debugging")
        
        # View skill with supporting files
        await skills(
            action="view",
            name="python-debugging",
            include_supporting_files=True
        )
        
        # Search for skills
        await skills(action="search", query="debug")
        
        # Search in content too
        await skills(action="search", query="pdb", search_content=True)
        
        # Get list of categories
        await skills(action="categories")
    """
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _skills_sync,
        action,
        name,
        query,
        category,
        include_disabled,
        include_supporting_files,
        search_content,
        platform_filter,
    )
    
    # Format result as JSON string
    return json.dumps(result, indent=2)


def _skills_sync(
    action: str,
    name: Optional[str],
    query: Optional[str],
    category: Optional[str],
    include_disabled: bool,
    include_supporting_files: bool,
    search_content: bool,
    platform_filter: bool,
) -> Dict[str, Any]:
    """Synchronous implementation of skills tool."""
    # Validate action
    valid_actions = {"list", "view", "search", "categories"}
    if action not in valid_actions:
        return {
            "success": False,
            "message": f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}",
        }
    
    # Route to appropriate handler
    try:
        if action == "list":
            return _list_skills(category, include_disabled, platform_filter)
        
        elif action == "view":
            if not name:
                return {"success": False, "message": "Missing required parameter: name"}
            return _view_skill(name, include_supporting_files)
        
        elif action == "search":
            if not query:
                return {"success": False, "message": "Missing required parameter: query"}
            return _search_skills(query, search_content, category)
        
        elif action == "categories":
            return _get_categories()
        
        else:
            return {"success": False, "message": f"Unimplemented action: {action}"}
    
    except Exception as e:
        logger.error(f"Skills tool error: {e}", exc_info=True)
        return {"success": False, "message": f"Unexpected error: {e}"}
