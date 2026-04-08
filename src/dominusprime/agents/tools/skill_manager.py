# -*- coding: utf-8 -*-
"""
Skill Manager Tool - Agent-facing tool for autonomous skill creation and management.

This tool allows agents to create, edit, patch, delete, and manage skills stored in
the ~/.dominusprime/skills/ directory. Each skill is a directory containing:
- SKILL.md: Main skill content with YAML frontmatter + Markdown body
- Optional subdirectories: references/, templates/, scripts/, assets/

Actions:
- create: Create new skill with SKILL.md and directory structure
- edit: Replace entire SKILL.md content
- patch: Targeted find-and-replace within SKILL.md or supporting files
- delete: Remove skill directory entirely
- write_file: Add/overwrite supporting file (reference, template, script, asset)
- remove_file: Remove supporting file

All operations include:
- Frontmatter validation (required: name, description)
- Platform compatibility checking
- Security scanning after writes
- Atomic file operations
"""

import asyncio
import logging
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..utils.skill_utils import (
    build_skill_path,
    extract_skill_conditions,
    extract_skill_description,
    find_skill_by_name,
    get_skill_subdirs,
    get_skills_directory,
    parse_frontmatter,
    skill_matches_platform,
    validate_skill_category,
    validate_skill_frontmatter,
    validate_skill_name,
)

logger = logging.getLogger(__name__)

# Security scanning patterns - block dangerous operations
SECURITY_PATTERNS = [
    # Shell command injection
    (r'subprocess\.(?:run|call|Popen|check_output)', 'subprocess execution'),
    (r'os\.system\s*\(', 'os.system() call'),
    (r'eval\s*\(', 'eval() call'),
    (r'exec\s*\(', 'exec() call'),
    (r'__import__\s*\(', '__import__() call'),
    
    # File system access outside skill directory
    (r'\.\./', 'directory traversal'),
    (r'open\s*\([^)]*["\']/', 'absolute path file access'),
    
    # Network operations
    (r'requests\.(?:get|post|put|delete)', 'HTTP requests'),
    (r'urllib\.request', 'URL requests'),
    (r'socket\.', 'socket operations'),
    
    # Dangerous imports
    (r'import\s+(?:subprocess|os|sys|shutil|socket)', 'dangerous imports'),
    (r'from\s+(?:subprocess|os|sys|shutil|socket)\s+import', 'dangerous imports'),
]


def _security_scan_skill(skill_dir: Path) -> Optional[str]:
    """
    Scan skill directory for dangerous patterns.
    
    Returns error message if blocked, None if safe.
    """
    try:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None
            
        content = skill_file.read_text(encoding="utf-8")
        
        # Check for dangerous patterns
        for pattern, description in SECURITY_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"Security scan blocked skill '{skill_dir.name}': {description}")
                return f"Security scan failed: detected {description}"
        
        # Scan supporting files
        for subdir_name in get_skill_subdirs():
            subdir = skill_dir / subdir_name
            if not subdir.exists():
                continue
                
            for file_path in subdir.rglob("*"):
                if not file_path.is_file():
                    continue
                    
                # Skip binary files
                try:
                    file_content = file_path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    continue
                
                for pattern, description in SECURITY_PATTERNS:
                    if re.search(pattern, file_content, re.IGNORECASE | re.MULTILINE):
                        logger.warning(
                            f"Security scan blocked file '{file_path.relative_to(skill_dir)}' "
                            f"in skill '{skill_dir.name}': {description}"
                        )
                        return f"Security scan failed in {file_path.name}: detected {description}"
        
        return None
        
    except Exception as e:
        logger.error(f"Security scan error for skill '{skill_dir.name}': {e}")
        return f"Security scan error: {e}"


def _validate_name(name: str) -> Optional[str]:
    """Validate skill name. Returns error message or None."""
    error = validate_skill_name(name)
    if error:
        return f"Invalid skill name: {error}"
    return None


def _validate_category(category: Optional[str]) -> Optional[str]:
    """Validate category name. Returns error message or None."""
    if category is None:
        return None
    error = validate_skill_category(category)
    if error:
        return f"Invalid category: {error}"
    return None


def _validate_frontmatter(content: str) -> Optional[str]:
    """
    Validate YAML frontmatter in skill content.
    
    Returns error message or None.
    """
    error = validate_skill_frontmatter(content)
    if error:
        return error
    
    # Additional validation: check platform compatibility
    try:
        frontmatter, _ = parse_frontmatter(content)
        if not skill_matches_platform(frontmatter):
            platforms = frontmatter.get("platforms", [])
            return (
                f"Skill is not compatible with current platform. "
                f"Required platforms: {platforms}"
            )
    except Exception as e:
        return f"Frontmatter parsing error: {e}"
    
    return None


def _resolve_skill_dir(name: str, category: str = None) -> Path:
    """Resolve skill directory path."""
    skills_dir = get_skills_directory()
    return build_skill_path(name, category, skills_dir)


def _find_skill(name: str) -> Optional[Dict[str, Any]]:
    """
    Find existing skill by name.
    
    Returns dict with 'path' and 'category' or None if not found.
    """
    skill_path = find_skill_by_name(name)
    if not skill_path:
        return None
    
    # Extract category from path
    skills_dir = get_skills_directory()
    rel_path = skill_path.relative_to(skills_dir)
    parts = rel_path.parts
    
    category = parts[0] if len(parts) > 1 else None
    
    return {"path": skill_path, "category": category}


def _validate_file_path(file_path: str) -> Optional[str]:
    """
    Validate supporting file path.
    
    Must be relative and within allowed subdirectories.
    Returns error message or None.
    """
    # Must be relative
    if file_path.startswith("/") or file_path.startswith("\\"):
        return "File path must be relative (no leading slash)"
    
    # No directory traversal
    if ".." in file_path:
        return "File path cannot contain '..'"
    
    # Must be in allowed subdirectory
    allowed_dirs = get_skill_subdirs()
    parts = Path(file_path).parts
    if not parts or parts[0] not in allowed_dirs:
        return f"File must be in one of: {', '.join(allowed_dirs)}"
    
    return None


def _atomic_write_text(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Atomically write text to file using temporary file + rename.
    
    Creates parent directories if needed.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file in same directory (ensures same filesystem)
    fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix=".tmp"
    )
    
    try:
        with open(fd, "w", encoding=encoding) as f:
            f.write(content)
        
        # Atomic rename
        temp_path_obj = Path(temp_path)
        temp_path_obj.replace(file_path)
        
    except Exception:
        # Clean up temp file on error
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass
        raise


# ============================================================================
# Action Implementations
# ============================================================================

def _create_skill(name: str, content: str, category: str = None) -> Dict[str, Any]:
    """
    Create new skill.
    
    Returns:
        {"success": bool, "message": str, "path": str}
    """
    # Validate name and category
    if error := _validate_name(name):
        return {"success": False, "message": error}
    
    if error := _validate_category(category):
        return {"success": False, "message": error}
    
    # Check if skill already exists
    if find_skill_by_name(name):
        return {"success": False, "message": f"Skill '{name}' already exists"}
    
    # Validate frontmatter
    if error := _validate_frontmatter(content):
        return {"success": False, "message": f"Invalid skill content: {error}"}
    
    # Create skill directory
    skill_dir = _resolve_skill_dir(name, category)
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return {"success": False, "message": f"Skill directory already exists: {skill_dir}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to create skill directory: {e}"}
    
    # Write SKILL.md
    skill_file = skill_dir / "SKILL.md"
    try:
        _atomic_write_text(skill_file, content)
    except Exception as e:
        # Clean up on failure
        shutil.rmtree(skill_dir, ignore_errors=True)
        return {"success": False, "message": f"Failed to write SKILL.md: {e}"}
    
    # Security scan
    if error := _security_scan_skill(skill_dir):
        shutil.rmtree(skill_dir, ignore_errors=True)
        return {"success": False, "message": error}
    
    logger.info(f"Created skill '{name}' at {skill_dir}")
    return {
        "success": True,
        "message": f"Successfully created skill '{name}'",
        "path": str(skill_dir),
    }


def _edit_skill(name: str, content: str) -> Dict[str, Any]:
    """
    Replace entire SKILL.md content.
    
    Returns:
        {"success": bool, "message": str, "path": str}
    """
    # Find existing skill
    skill_info = _find_skill(name)
    if not skill_info:
        return {"success": False, "message": f"Skill '{name}' not found"}
    
    skill_dir = skill_info["path"]
    
    # Validate frontmatter
    if error := _validate_frontmatter(content):
        return {"success": False, "message": f"Invalid skill content: {error}"}
    
    # Write SKILL.md
    skill_file = skill_dir / "SKILL.md"
    try:
        _atomic_write_text(skill_file, content)
    except Exception as e:
        return {"success": False, "message": f"Failed to write SKILL.md: {e}"}
    
    # Security scan
    if error := _security_scan_skill(skill_dir):
        return {"success": False, "message": error}
    
    logger.info(f"Edited skill '{name}' at {skill_dir}")
    return {
        "success": True,
        "message": f"Successfully edited skill '{name}'",
        "path": str(skill_dir),
    }


def _patch_skill(
    name: str,
    file_path: Optional[str],
    find: str,
    replace: str,
) -> Dict[str, Any]:
    """
    Targeted find-and-replace within SKILL.md or supporting file.
    
    Args:
        name: Skill name
        file_path: Relative path to file (None = SKILL.md)
        find: Text to find (literal or regex if starts with 'regex:')
        replace: Replacement text
    
    Returns:
        {"success": bool, "message": str, "path": str, "matches": int}
    """
    # Find existing skill
    skill_info = _find_skill(name)
    if not skill_info:
        return {"success": False, "message": f"Skill '{name}' not found"}
    
    skill_dir = skill_info["path"]
    
    # Determine target file
    if file_path is None:
        target_file = skill_dir / "SKILL.md"
    else:
        # Validate file path
        if error := _validate_file_path(file_path):
            return {"success": False, "message": error}
        target_file = skill_dir / file_path
    
    # Check file exists
    if not target_file.exists():
        return {
            "success": False,
            "message": f"File not found: {file_path or 'SKILL.md'}",
        }
    
    # Read current content
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        return {"success": False, "message": f"Failed to read file: {e}"}
    
    # Perform replacement
    is_regex = find.startswith("regex:")
    if is_regex:
        pattern = find[6:]  # Remove 'regex:' prefix
        try:
            new_content, num_matches = re.subn(pattern, replace, content)
        except re.error as e:
            return {"success": False, "message": f"Invalid regex pattern: {e}"}
    else:
        # Literal replacement
        num_matches = content.count(find)
        new_content = content.replace(find, replace)
    
    if num_matches == 0:
        return {
            "success": False,
            "message": f"Pattern not found in {file_path or 'SKILL.md'}",
        }
    
    # Validate frontmatter if editing SKILL.md
    if file_path is None:
        if error := _validate_frontmatter(new_content):
            return {"success": False, "message": f"Patch would break frontmatter: {error}"}
    
    # Write updated content
    try:
        _atomic_write_text(target_file, new_content)
    except Exception as e:
        return {"success": False, "message": f"Failed to write file: {e}"}
    
    # Security scan
    if error := _security_scan_skill(skill_dir):
        return {"success": False, "message": error}
    
    logger.info(f"Patched skill '{name}' file '{file_path or 'SKILL.md'}' ({num_matches} matches)")
    return {
        "success": True,
        "message": f"Successfully patched {file_path or 'SKILL.md'} ({num_matches} matches)",
        "path": str(skill_dir),
        "matches": num_matches,
    }


def _delete_skill(name: str) -> Dict[str, Any]:
    """
    Delete skill directory entirely.
    
    Returns:
        {"success": bool, "message": str}
    """
    # Find existing skill
    skill_info = _find_skill(name)
    if not skill_info:
        return {"success": False, "message": f"Skill '{name}' not found"}
    
    skill_dir = skill_info["path"]
    
    # Delete directory
    try:
        shutil.rmtree(skill_dir)
    except Exception as e:
        return {"success": False, "message": f"Failed to delete skill: {e}"}
    
    logger.info(f"Deleted skill '{name}' from {skill_dir}")
    return {
        "success": True,
        "message": f"Successfully deleted skill '{name}'",
    }


def _write_file(name: str, file_path: str, file_content: str) -> Dict[str, Any]:
    """
    Add/overwrite supporting file.
    
    Args:
        name: Skill name
        file_path: Relative path within skill (e.g., 'references/example.md')
        file_content: File content
    
    Returns:
        {"success": bool, "message": str, "path": str}
    """
    # Find existing skill
    skill_info = _find_skill(name)
    if not skill_info:
        return {"success": False, "message": f"Skill '{name}' not found"}
    
    skill_dir = skill_info["path"]
    
    # Validate file path
    if error := _validate_file_path(file_path):
        return {"success": False, "message": error}
    
    # Write file
    target_file = skill_dir / file_path
    try:
        _atomic_write_text(target_file, file_content)
    except Exception as e:
        return {"success": False, "message": f"Failed to write file: {e}"}
    
    # Security scan
    if error := _security_scan_skill(skill_dir):
        # Remove the file we just wrote
        try:
            target_file.unlink()
        except Exception:
            pass
        return {"success": False, "message": error}
    
    logger.info(f"Wrote file '{file_path}' to skill '{name}'")
    return {
        "success": True,
        "message": f"Successfully wrote {file_path}",
        "path": str(target_file),
    }


def _remove_file(name: str, file_path: str) -> Dict[str, Any]:
    """
    Remove supporting file.
    
    Args:
        name: Skill name
        file_path: Relative path within skill
    
    Returns:
        {"success": bool, "message": str}
    """
    # Find existing skill
    skill_info = _find_skill(name)
    if not skill_info:
        return {"success": False, "message": f"Skill '{name}' not found"}
    
    skill_dir = skill_info["path"]
    
    # Validate file path
    if error := _validate_file_path(file_path):
        return {"success": False, "message": error}
    
    # Check file exists
    target_file = skill_dir / file_path
    if not target_file.exists():
        return {"success": False, "message": f"File not found: {file_path}"}
    
    # Cannot remove SKILL.md via this action
    if target_file.name == "SKILL.md":
        return {
            "success": False,
            "message": "Cannot remove SKILL.md (use 'delete' action to remove entire skill)",
        }
    
    # Remove file
    try:
        target_file.unlink()
    except Exception as e:
        return {"success": False, "message": f"Failed to remove file: {e}"}
    
    logger.info(f"Removed file '{file_path}' from skill '{name}'")
    return {
        "success": True,
        "message": f"Successfully removed {file_path}",
    }


# ============================================================================
# Main Tool Function
# ============================================================================

async def skill_manage(
    action: str,
    name: str,
    content: Optional[str] = None,
    category: Optional[str] = None,
    file_path: Optional[str] = None,
    find: Optional[str] = None,
    replace: Optional[str] = None,
) -> str:
    """
    Manage skills: create, edit, patch, delete, write_file, remove_file.
    
    Args:
        action: Action to perform (create|edit|patch|delete|write_file|remove_file)
        name: Skill name (lowercase, alphanumeric, hyphens, dots, underscores)
        content: Skill content (for create/edit) or file content (for write_file)
        category: Category name (optional, for create only)
        file_path: Relative file path within skill (for patch/write_file/remove_file)
        find: Text to find (for patch) - prefix with 'regex:' for regex matching
        replace: Replacement text (for patch)
    
    Returns:
        JSON-formatted result string with success status and message.
    
    Examples:
        # Create a new debugging skill
        await skill_manage(
            action="create",
            name="python-debugging",
            category="development",
            content='''---
name: python-debugging
description: Step-by-step guide for debugging Python applications
platforms: [linux, macos, windows]
---
# Python Debugging Skill

## When to Use
- Python script is crashing
- Unexpected behavior in Python code
- Need to trace execution flow

## Steps
1. Add print statements or use pdb
2. Check error messages and stack traces
3. Use logging module for persistent debugging
4. Run with python -i for interactive mode
'''
        )
        
        # Edit existing skill
        await skill_manage(
            action="edit",
            name="python-debugging",
            content="<updated content>"
        )
        
        # Patch a specific section
        await skill_manage(
            action="patch",
            name="python-debugging",
            find="## Steps",
            replace="## Debugging Steps"
        )
        
        # Add a reference file
        await skill_manage(
            action="write_file",
            name="python-debugging",
            file_path="references/pdb-commands.md",
            content="# PDB Commands\n- n: next line\n- s: step into\n- c: continue"
        )
        
        # Remove a file
        await skill_manage(
            action="remove_file",
            name="python-debugging",
            file_path="references/old-notes.md"
        )
        
        # Delete entire skill
        await skill_manage(action="delete", name="python-debugging")
    """
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _skill_manage_sync,
        action,
        name,
        content,
        category,
        file_path,
        find,
        replace,
    )
    
    # Format result as JSON string
    import json
    return json.dumps(result, indent=2)


def _skill_manage_sync(
    action: str,
    name: str,
    content: Optional[str],
    category: Optional[str],
    file_path: Optional[str],
    find: Optional[str],
    replace: Optional[str],
) -> Dict[str, Any]:
    """Synchronous implementation of skill_manage."""
    # Validate action
    valid_actions = {"create", "edit", "patch", "delete", "write_file", "remove_file"}
    if action not in valid_actions:
        return {
            "success": False,
            "message": f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}",
        }
    
    # Route to appropriate handler
    try:
        if action == "create":
            if not content:
                return {"success": False, "message": "Missing required parameter: content"}
            return _create_skill(name, content, category)
        
        elif action == "edit":
            if not content:
                return {"success": False, "message": "Missing required parameter: content"}
            return _edit_skill(name, content)
        
        elif action == "patch":
            if not find or replace is None:
                return {"success": False, "message": "Missing required parameters: find, replace"}
            return _patch_skill(name, file_path, find, replace)
        
        elif action == "delete":
            return _delete_skill(name)
        
        elif action == "write_file":
            if not file_path or not content:
                return {"success": False, "message": "Missing required parameters: file_path, content"}
            return _write_file(name, file_path, content)
        
        elif action == "remove_file":
            if not file_path:
                return {"success": False, "message": "Missing required parameter: file_path"}
            return _remove_file(name, file_path)
        
        else:
            return {"success": False, "message": f"Unimplemented action: {action}"}
    
    except Exception as e:
        logger.error(f"Skill management error: {e}", exc_info=True)
        return {"success": False, "message": f"Unexpected error: {e}"}
