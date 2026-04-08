# -*- coding: utf-8 -*-
"""
Skill utilities for parsing, validation, and metadata extraction.

Based on hermes-agent's skills system, adapted for DominusPrime.
"""

import logging
import os
import platform
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Set, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Excluded directories when scanning skills
EXCLUDED_SKILL_DIRS = {'.git', '.github', '.hub', '__pycache__', 'node_modules', '.venv', 'venv'}


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from skill markdown content.
    
    Args:
        content: Raw markdown content with frontmatter
        
    Returns:
        Tuple of (frontmatter_dict, body_content)
        
    Example:
        >>> content = '''---
        ... name: My Skill
        ... description: Does something
        ... ---
        ... # Instructions
        ... Do this...'''
        >>> fm, body = parse_frontmatter(content)
        >>> fm['name']
        'My Skill'
    """
    if not content.strip():
        return {}, ""
    
    if not content.startswith("---"):
        # No frontmatter, treat entire content as body
        return {}, content
    
    # Find closing ---
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        # Invalid frontmatter, treat as body
        logger.debug("Invalid frontmatter format (no closing ---)")
        return {}, content
    
    # Extract YAML content
    yaml_content = content[3:end_match.start() + 3]
    body = content[end_match.end() + 3:]
    
    try:
        frontmatter = yaml.safe_load(yaml_content)
        if not isinstance(frontmatter, dict):
            logger.debug("Frontmatter is not a dict, treating as empty")
            return {}, content
        return frontmatter, body
    except yaml.YAMLError as e:
        logger.debug("YAML parse error: %s", e)
        return {}, content


def skill_matches_platform(frontmatter: Dict[str, Any]) -> bool:
    """
    Check if a skill is compatible with the current OS platform.
    
    Skills can declare platform requirements via a 'platforms' list in frontmatter:
        platforms: [linux, macos]
    
    If 'platforms' is absent or empty, the skill is compatible with all platforms.
    
    Args:
        frontmatter: Parsed skill frontmatter dict
        
    Returns:
        True if skill is compatible with current platform
    """
    platforms = frontmatter.get("platforms")
    if not platforms:
        # No platform restriction
        return True
    
    if not isinstance(platforms, (list, tuple)):
        platforms = [platforms]
    
    # Normalize platform names
    current = platform.system().lower()
    platform_map = {
        "darwin": "macos",
        "linux": "linux",
        "windows": "windows",
    }
    resolved = platform_map.get(current, current)
    
    normalized_platforms = {
        str(p).strip().lower() for p in platforms if str(p).strip()
    }
    
    return resolved in normalized_platforms


def extract_skill_description(frontmatter: Dict[str, Any], max_length: int = 200) -> str:
    """
    Extract a truncated description from skill frontmatter.
    
    Args:
        frontmatter: Parsed skill frontmatter
        max_length: Maximum description length
        
    Returns:
        Truncated description string
    """
    desc = str(frontmatter.get("description", "")).strip()
    if not desc:
        return ""
    
    if len(desc) <= max_length:
        return desc
    
    # Truncate at word boundary
    truncated = desc[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:  # Only truncate if we're reasonably close
        truncated = truncated[:last_space]
    
    return truncated + "..."


def extract_skill_conditions(frontmatter: Dict[str, Any]) -> Dict[str, List]:
    """
    Extract conditional activation fields from skill frontmatter.
    
    Skills can specify requirements:
        required_tools: [terminal, file, web_search]
        required_toolsets: [development, web]
    
    Args:
        frontmatter: Parsed skill frontmatter
        
    Returns:
        Dict with 'required_tools' and 'required_toolsets' lists
    """
    conditions = {
        "required_tools": [],
        "required_toolsets": [],
    }
    
    for key in ("required_tools", "required_toolsets"):
        value = frontmatter.get(key)
        if not value:
            continue
        if isinstance(value, str):
            conditions[key] = [v.strip() for v in value.split(",") if v.strip()]
        elif isinstance(value, (list, tuple)):
            conditions[key] = [str(v).strip() for v in value if str(v).strip()]
    
    return conditions


def validate_skill_name(name: str, max_length: int = 64) -> Optional[str]:
    """
    Validate a skill name for filesystem and URL safety.
    
    Args:
        name: Skill name to validate
        max_length: Maximum allowed length
        
    Returns:
        None if valid, error message string if invalid
        
    Rules:
        - Must start with letter or digit
        - Can contain: a-z, 0-9, hyphens, dots, underscores
        - Must be lowercase
        - No spaces or special characters
    """
    if not name:
        return "Skill name is required"
    
    if len(name) > max_length:
        return f"Skill name exceeds {max_length} characters"
    
    if not re.match(r'^[a-z0-9][a-z0-9._-]*$', name):
        return (
            f"Invalid skill name '{name}'. Use lowercase letters, numbers, "
            "hyphens, dots, and underscores. Must start with letter or digit."
        )
    
    return None


def validate_skill_category(category: Optional[str], max_length: int = 64) -> Optional[str]:
    """
    Validate an optional category name used as a directory segment.
    
    Args:
        category: Category name to validate (can be None)
        max_length: Maximum allowed length
        
    Returns:
        None if valid, error message string if invalid
    """
    if category is None:
        return None
    
    if not isinstance(category, str):
        return "Category must be a string"
    
    category = category.strip()
    if not category:
        return None
    
    if "/" in category or "\\" in category:
        return (
            "Invalid category. Use lowercase letters, numbers, "
            "hyphens, dots, and underscores. Must be a single directory name."
        )
    
    if len(category) > max_length:
        return f"Category exceeds {max_length} characters"
    
    if not re.match(r'^[a-z0-9][a-z0-9._-]*$', category):
        return (
            "Invalid category. Use lowercase letters, numbers, "
            "hyphens, dots, and underscores. Must start with letter or digit."
        )
    
    return None


def validate_skill_frontmatter(content: str, max_desc_length: int = 1024) -> Optional[str]:
    """
    Validate that SKILL.md content has proper frontmatter with required fields.
    
    Args:
        content: Full SKILL.md content
        max_desc_length: Maximum description length
        
    Returns:
        None if valid, error message string if invalid
        
    Required fields:
        - name: Display name
        - description: What the skill does
    """
    if not content.strip():
        return "Content cannot be empty"
    
    if not content.startswith("---"):
        return "SKILL.md must start with YAML frontmatter (---)"
    
    frontmatter, body = parse_frontmatter(content)
    
    if "name" not in frontmatter:
        return "Frontmatter must include 'name' field"
    
    if "description" not in frontmatter:
        return "Frontmatter must include 'description' field"
    
    desc = str(frontmatter["description"])
    if len(desc) > max_desc_length:
        return f"Description exceeds {max_desc_length} characters"
    
    if not body.strip():
        return "SKILL.md must have content after frontmatter"
    
    return None


def get_disabled_skill_names(config: Optional[Dict[str, Any]] = None) -> Set[str]:
    """
    Get set of disabled skill names from configuration.
    
    Args:
        config: Configuration dict (if None, loads from default location)
        
    Returns:
        Set of disabled skill names
    """
    if config is None:
        try:
            from ...config.config import load_config
            config = load_config()
        except Exception as e:
            logger.debug("Could not load config for disabled skills: %s", e)
            return set()
    
    skills_config = config.get("skills", {})
    if not isinstance(skills_config, dict):
        return set()
    
    disabled = skills_config.get("disabled", [])
    if not disabled:
        return set()
    
    if isinstance(disabled, str):
        return {disabled.strip()}
    
    return {str(name).strip() for name in disabled if str(name).strip()}


def get_skills_directory() -> Path:
    """
    Get the skills directory path.
    
    Returns:
        Path to ~/.dominusprime/skills/
    """
    return Path.home() / ".dominusprime" / "skills"


def iter_skill_files(skills_dir: Path, filename: str = "SKILL.md"):
    """
    Walk skills directory yielding sorted paths matching filename.
    
    Args:
        skills_dir: Root skills directory
        filename: File to search for (default: SKILL.md)
        
    Yields:
        Path objects for matching files
    """
    if not skills_dir.exists():
        return
    
    matches = []
    for root, dirs, files in os.walk(skills_dir):
        # Exclude certain directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_SKILL_DIRS]
        
        if filename in files:
            matches.append(Path(root) / filename)
    
    # Sort by relative path for consistency
    for path in sorted(matches, key=lambda p: str(p.relative_to(skills_dir))):
        yield path


def find_skill_by_name(name: str, skills_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find a skill directory by name.
    
    Args:
        name: Skill name to find
        skills_dir: Skills directory to search (default: ~/.dominusprime/skills)
        
    Returns:
        Path to skill directory, or None if not found
    """
    if skills_dir is None:
        skills_dir = get_skills_directory()
    
    if not skills_dir.exists():
        return None
    
    for skill_file in iter_skill_files(skills_dir):
        if skill_file.parent.name == name:
            return skill_file.parent
    
    return None


def build_skill_path(name: str, category: Optional[str] = None, 
                     skills_dir: Optional[Path] = None) -> Path:
    """
    Build the directory path for a skill, optionally under a category.
    
    Args:
        name: Skill name
        category: Optional category (subdirectory)
        skills_dir: Skills directory (default: ~/.dominusprime/skills)
        
    Returns:
        Path to skill directory
    """
    if skills_dir is None:
        skills_dir = get_skills_directory()
    
    if category:
        return skills_dir / category / name
    return skills_dir / name


def get_skill_subdirs() -> Set[str]:
    """
    Get allowed subdirectories for skill supporting files.
    
    Returns:
        Set of allowed subdirectory names
    """
    return {"references", "templates", "scripts", "assets"}
