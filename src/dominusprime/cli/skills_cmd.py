# -*- coding: utf-8 -*-
"""CLI commands for managing skills in the new skills system."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click

from ..agents.tools.skill_manager import skill_manage
from ..agents.tools.skills_tool import skills
from ..agents.utils.skill_utils import get_skills_directory
from .utils import prompt_confirm


@click.group("skills")
def skills_group() -> None:
    """Manage agent skills (list, view, search, create, edit, delete)."""


@skills_group.command("list")
@click.option(
    "--category",
    "-c",
    type=str,
    default=None,
    help="Filter by category",
)
@click.option(
    "--include-disabled",
    is_flag=True,
    help="Include disabled skills",
)
@click.option(
    "--no-platform-filter",
    is_flag=True,
    help="Show skills for all platforms (ignore compatibility)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def list_cmd(
    category: Optional[str],
    include_disabled: bool,
    no_platform_filter: bool,
    output_json: bool,
) -> None:
    """List all available skills."""
    try:
        result_str = asyncio.run(
            skills(
                action="list",
                category=category,
                include_disabled=include_disabled,
                platform_filter=not no_platform_filter,
            )
        )
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: {result.get('message', 'Unknown error')}", err=True)
            sys.exit(1)
        
        skill_list = result.get("skills", [])
        count = result.get("count", 0)
        
        if output_json:
            click.echo(json.dumps(result, indent=2))
            return
        
        if count == 0:
            click.echo("No skills found.")
            return
        
        # Display table
        click.echo(f"\n{'─' * 80}")
        click.echo(
            f"  {'Name':<25s} {'Category':<20s} {'Platforms':<15s} {'Status'}"
        )
        click.echo(f"{'─' * 80}")
        
        for skill in skill_list:
            name = skill.get("name", "")
            cat = skill.get("category") or "uncategorized"
            platforms = ", ".join(skill.get("platforms", [])) or "all"
            disabled = skill.get("disabled", False)
            
            if len(platforms) > 14:
                platforms = platforms[:11] + "..."
            
            status = (
                click.style("✗ disabled", fg="red")
                if disabled
                else click.style("✓ enabled", fg="green")
            )
            
            click.echo(f"  {name:<25s} {cat:<20s} {platforms:<15s} {status}")
        
        click.echo(f"{'─' * 80}")
        enabled_count = sum(1 for s in skill_list if not s.get("disabled"))
        click.echo(
            f"  Total: {count} skills, "
            f"{enabled_count} enabled, "
            f"{count - enabled_count} disabled\n"
        )
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("view")
@click.argument("name", type=str)
@click.option(
    "--include-files",
    is_flag=True,
    help="Include supporting files (references, templates, scripts, assets)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def view_cmd(name: str, include_files: bool, output_json: bool) -> None:
    """View skill content."""
    try:
        result_str = asyncio.run(
            skills(
                action="view",
                name=name,
                include_supporting_files=include_files,
            )
        )
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: {result.get('message', 'Skill not found')}", err=True)
            sys.exit(1)
        
        if output_json:
            click.echo(json.dumps(result, indent=2))
            return
        
        # Display skill content
        skill_name = result.get("name", "")
        category = result.get("category") or "uncategorized"
        content = result.get("content", "")
        frontmatter = result.get("frontmatter", {})
        
        click.echo(f"\n{'=' * 80}")
        click.echo(f"Skill: {skill_name}")
        click.echo(f"Category: {category}")
        click.echo(f"{'=' * 80}\n")
        
        # Show frontmatter
        click.echo(click.style("Frontmatter:", bold=True))
        for key, value in frontmatter.items():
            click.echo(f"  {key}: {value}")
        click.echo()
        
        # Show content
        click.echo(click.style("Content:", bold=True))
        click.echo(content)
        
        # Show supporting files if requested
        if include_files and "supporting_files" in result:
            files = result["supporting_files"]
            if files:
                click.echo(f"\n{'─' * 80}")
                click.echo(click.style(f"Supporting Files ({len(files)}):", bold=True))
                for file in files:
                    file_path = file.get("path", "")
                    size = file.get("size", 0)
                    file_content = file.get("content", "")
                    
                    click.echo(f"\n  📄 {file_path} ({size} bytes)")
                    if file_content != "<file too large to display>" and file_content != "<binary file>":
                        click.echo(f"  {'-' * 76}")
                        click.echo(file_content)
                    else:
                        click.echo(f"  {file_content}")
        
        click.echo()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("search")
@click.argument("query", type=str)
@click.option(
    "--content",
    is_flag=True,
    help="Search in skill body content (slower)",
)
@click.option(
    "--category",
    "-c",
    type=str,
    default=None,
    help="Filter by category",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def search_cmd(
    query: str,
    content: bool,
    category: Optional[str],
    output_json: bool,
) -> None:
    """Search skills by name, description, or content."""
    try:
        result_str = asyncio.run(
            skills(
                action="search",
                query=query,
                search_content=content,
                category=category,
            )
        )
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: {result.get('message', 'Unknown error')}", err=True)
            sys.exit(1)
        
        results_list = result.get("results", [])
        count = result.get("count", 0)
        
        if output_json:
            click.echo(json.dumps(result, indent=2))
            return
        
        if count == 0:
            click.echo(f"No skills found matching '{query}'.")
            return
        
        # Display results
        click.echo(f"\nFound {count} skill(s) matching '{query}':\n")
        click.echo(f"{'─' * 80}")
        
        for i, skill in enumerate(results_list, 1):
            name = skill.get("name", "")
            cat = skill.get("category") or "uncategorized"
            description = skill.get("description", "")
            match_type = skill.get("match_type", "metadata")
            
            click.echo(f"{i}. {click.style(name, bold=True, fg='cyan')} ({cat})")
            click.echo(f"   {description}")
            click.echo(f"   Match: {match_type}")
            if i < count:
                click.echo()
        
        click.echo(f"{'─' * 80}\n")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("categories")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def categories_cmd(output_json: bool) -> None:
    """List all skill categories."""
    try:
        result_str = asyncio.run(skills(action="categories"))
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: {result.get('message', 'Unknown error')}", err=True)
            sys.exit(1)
        
        categories_list = result.get("categories", [])
        count = result.get("count", 0)
        
        if output_json:
            click.echo(json.dumps(result, indent=2))
            return
        
        if count == 0:
            click.echo("No categories found.")
            return
        
        click.echo(f"\nSkill Categories ({count}):\n")
        for cat in categories_list:
            click.echo(f"  • {cat}")
        click.echo()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("create")
@click.argument("name", type=str)
@click.option(
    "--category",
    "-c",
    type=str,
    default=None,
    help="Skill category",
)
@click.option(
    "--editor",
    is_flag=True,
    help="Open editor to write skill content",
)
def create_cmd(name: str, category: Optional[str], editor: bool) -> None:
    """Create a new skill."""
    try:
        # Get content
        if editor:
            import tempfile
            
            # Create template
            template = f"""---
name: {name}
description: Brief description of what this skill does (required)
platforms: [linux, macos, windows]
required_tools: []
tags: []
author: DominusPrime
version: 1.0.0
---

# {name.replace('-', ' ').title()}

## Overview

Brief overview of the skill...

## When to Use

- Scenario 1
- Scenario 2

## Steps

1. Step one
2. Step two
3. Step three

## Examples

```
Example code or commands here
```

## Related Skills

- skill-name-1
- skill-name-2
"""
            
            # Write to temp file and open editor
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(template)
                temp_path = f.name
            
            # Open editor
            click.edit(filename=temp_path)
            
            # Read back
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Clean up
            Path(temp_path).unlink()
        else:
            # Prompt for content
            click.echo("Enter skill content (YAML frontmatter + Markdown).")
            click.echo("Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done:\n")
            content = sys.stdin.read()
        
        if not content.strip():
            click.echo("Error: No content provided.", err=True)
            sys.exit(1)
        
        # Create skill
        result_str = asyncio.run(
            skill_manage(
                action="create",
                name=name,
                category=category,
                content=content,
            )
        )
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: {result.get('message', 'Unknown error')}", err=True)
            sys.exit(1)
        
        click.echo(click.style(f"✓ {result.get('message')}", fg="green"))
        click.echo(f"  Path: {result.get('path')}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("edit")
@click.argument("name", type=str)
def edit_cmd(name: str) -> None:
    """Edit an existing skill in your default editor."""
    try:
        # First, view the skill to get current content
        result_str = asyncio.run(skills(action="view", name=name))
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: Skill '{name}' not found.", err=True)
            sys.exit(1)
        
        current_content = result.get("content", "")
        
        # Open editor
        new_content = click.edit(current_content)
        
        if new_content is None or new_content.strip() == current_content.strip():
            click.echo("No changes made.")
            return
        
        # Confirm
        if not prompt_confirm("Save changes?", default=True):
            click.echo("Changes discarded.")
            return
        
        # Save changes
        result_str = asyncio.run(
            skill_manage(
                action="edit",
                name=name,
                content=new_content,
            )
        )
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: {result.get('message', 'Unknown error')}", err=True)
            sys.exit(1)
        
        click.echo(click.style(f"✓ {result.get('message')}", fg="green"))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("delete")
@click.argument("name", type=str)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation",
)
def delete_cmd(name: str, force: bool) -> None:
    """Delete a skill."""
    try:
        if not force:
            if not prompt_confirm(f"Delete skill '{name}'? This cannot be undone.", default=False):
                click.echo("Cancelled.")
                return
        
        result_str = asyncio.run(skill_manage(action="delete", name=name))
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: {result.get('message', 'Unknown error')}", err=True)
            sys.exit(1)
        
        click.echo(click.style(f"✓ {result.get('message')}", fg="green"))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("disable")
@click.argument("name", type=str)
def disable_cmd(name: str) -> None:
    """Disable a skill (adds to disabled list in config)."""
    try:
        from ..config.config import load_config, save_config
        
        config = load_config()
        
        # Ensure skills section exists
        if "skills" not in config:
            config["skills"] = {}
        if "disabled" not in config["skills"]:
            config["skills"]["disabled"] = []
        
        disabled_list = config["skills"]["disabled"]
        
        if name in disabled_list:
            click.echo(f"Skill '{name}' is already disabled.")
            return
        
        # Verify skill exists
        result_str = asyncio.run(skills(action="view", name=name))
        result = json.loads(result_str)
        
        if not result.get("success"):
            click.echo(f"Error: Skill '{name}' not found.", err=True)
            sys.exit(1)
        
        # Add to disabled list
        disabled_list.append(name)
        save_config(config)
        
        click.echo(click.style(f"✓ Disabled skill '{name}'", fg="green"))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("enable")
@click.argument("name", type=str)
def enable_cmd(name: str) -> None:
    """Enable a previously disabled skill."""
    try:
        from ..config.config import load_config, save_config
        
        config = load_config()
        
        if "skills" not in config or "disabled" not in config["skills"]:
            click.echo(f"Skill '{name}' is not disabled.")
            return
        
        disabled_list = config["skills"]["disabled"]
        
        if name not in disabled_list:
            click.echo(f"Skill '{name}' is not disabled.")
            return
        
        # Remove from disabled list
        disabled_list.remove(name)
        save_config(config)
        
        click.echo(click.style(f"✓ Enabled skill '{name}'", fg="green"))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@skills_group.command("path")
def path_cmd() -> None:
    """Show the skills directory path."""
    skills_dir = get_skills_directory()
    click.echo(f"Skills directory: {skills_dir}")
    
    if skills_dir.exists():
        # Count skills
        skill_count = sum(1 for _ in skills_dir.rglob("SKILL.md"))
        click.echo(f"  Skills found: {skill_count}")
    else:
        click.echo("  Directory does not exist yet (will be created on first use)")


@skills_group.command("init")
def init_cmd() -> None:
    """Initialize the skills directory with example skills."""
    try:
        skills_dir = get_skills_directory()
        
        if skills_dir.exists():
            skill_count = sum(1 for _ in skills_dir.rglob("SKILL.md"))
            if skill_count > 0:
                if not prompt_confirm(
                    f"Skills directory already contains {skill_count} skill(s). Continue?",
                    default=False
                ):
                    click.echo("Cancelled.")
                    return
        
        # Create directory
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy example skills from examples/skills/ to ~/.dominusprime/skills/
        import shutil
        from pathlib import Path
        
        # Get project root (where examples/ is)
        # Assuming CLI is at src/dominusprime/cli/skills_cmd.py
        # Project root is 3 levels up
        project_root = Path(__file__).parent.parent.parent.parent
        examples_dir = project_root / "examples" / "skills"
        
        if not examples_dir.exists():
            click.echo(f"Warning: Example skills not found at {examples_dir}")
            click.echo(f"Created empty skills directory at {skills_dir}")
            return
        
        # Copy all example skills
        copied = 0
        for skill_dir in examples_dir.rglob("*/"):
            if (skill_dir / "SKILL.md").exists():
                # This is a skill directory
                rel_path = skill_dir.relative_to(examples_dir)
                dest_dir = skills_dir / rel_path
                
                if dest_dir.exists():
                    click.echo(f"  Skipping {rel_path} (already exists)")
                else:
                    shutil.copytree(skill_dir, dest_dir)
                    click.echo(f"  ✓ Copied {rel_path}")
                    copied += 1
        
        click.echo(click.style(f"\n✓ Initialized skills directory", fg="green"))
        click.echo(f"  Location: {skills_dir}")
        click.echo(f"  Copied {copied} example skill(s)")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
