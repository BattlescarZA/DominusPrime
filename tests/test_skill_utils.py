# -*- coding: utf-8 -*-
"""Unit tests for skill_utils module."""
import platform
import tempfile
from pathlib import Path

import pytest

from dominusprime.agents.utils.skill_utils import (
    build_skill_path,
    extract_skill_conditions,
    extract_skill_description,
    find_skill_by_name,
    get_disabled_skill_names,
    get_skill_subdirs,
    get_skills_directory,
    iter_skill_files,
    parse_frontmatter,
    skill_matches_platform,
    validate_skill_category,
    validate_skill_frontmatter,
    validate_skill_name,
)


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""
    
    def test_valid_frontmatter(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
name: test-skill
description: Test skill
platforms: [linux]
---

# Test Skill

Body content here.
"""
        frontmatter, body = parse_frontmatter(content)
        
        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "Test skill"
        assert frontmatter["platforms"] == ["linux"]
        assert "# Test Skill" in body
        assert "Body content here" in body
    
    def test_no_frontmatter(self):
        """Test content with no frontmatter."""
        content = "# Just a heading\n\nSome content"
        
        frontmatter, body = parse_frontmatter(content)
        
        assert frontmatter == {}
        assert body == content
    
    def test_empty_frontmatter(self):
        """Test empty frontmatter."""
        content = "---\n---\n\nBody"
        
        frontmatter, body = parse_frontmatter(content)
        
        assert frontmatter == {}
        assert "Body" in body
    
    def test_complex_frontmatter(self):
        """Test complex YAML structures."""
        content = """---
name: complex
description: Complex skill
platforms:
  - linux
  - macos
required_tools:
  - tool1
  - tool2
metadata:
  author: DominusPrime
  version: 1.0.0
---

Body
"""
        frontmatter, body = parse_frontmatter(content)
        
        assert frontmatter["name"] == "complex"
        assert len(frontmatter["platforms"]) == 2
        assert frontmatter["metadata"]["author"] == "DominusPrime"


class TestSkillMatchesPlatform:
    """Tests for skill_matches_platform function."""
    
    def test_no_platforms_specified(self):
        """Test skill with no platform restrictions."""
        frontmatter = {"name": "test"}
        assert skill_matches_platform(frontmatter) is True
    
    def test_empty_platforms_list(self):
        """Test skill with empty platforms list."""
        frontmatter = {"platforms": []}
        assert skill_matches_platform(frontmatter) is True
    
    def test_matching_platform(self):
        """Test skill with matching platform."""
        current_os = platform.system().lower()
        if current_os == "darwin":
            current_os = "macos"
        
        frontmatter = {"platforms": [current_os]}
        assert skill_matches_platform(frontmatter) is True
    
    def test_non_matching_platform(self):
        """Test skill with non-matching platform."""
        current_os = platform.system().lower()
        if current_os == "darwin":
            current_os = "macos"
        
        # Pick a different platform
        other_platform = "windows" if current_os != "windows" else "linux"
        
        frontmatter = {"platforms": [other_platform]}
        assert skill_matches_platform(frontmatter) is False
    
    def test_multiple_platforms(self):
        """Test skill with multiple platforms."""
        frontmatter = {"platforms": ["linux", "macos", "windows"]}
        assert skill_matches_platform(frontmatter) is True


class TestExtractSkillDescription:
    """Tests for extract_skill_description function."""
    
    def test_short_description(self):
        """Test description shorter than max length."""
        frontmatter = {"description": "Short description"}
        desc = extract_skill_description(frontmatter, max_length=200)
        assert desc == "Short description"
    
    def test_long_description_truncation(self):
        """Test truncation of long description."""
        long_desc = "x" * 250
        frontmatter = {"description": long_desc}
        desc = extract_skill_description(frontmatter, max_length=200)
        
        assert len(desc) <= 203  # 200 + "..."
        assert desc.endswith("...")
    
    def test_missing_description(self):
        """Test with missing description."""
        frontmatter = {"name": "test"}
        desc = extract_skill_description(frontmatter)
        assert desc == ""
    
    def test_exact_max_length(self):
        """Test description at exact max length."""
        frontmatter = {"description": "x" * 200}
        desc = extract_skill_description(frontmatter, max_length=200)
        assert len(desc) == 200
        assert not desc.endswith("...")


class TestExtractSkillConditions:
    """Tests for extract_skill_conditions function."""
    
    def test_with_required_tools(self):
        """Test extraction of required_tools."""
        frontmatter = {
            "required_tools": ["tool1", "tool2"],
            "required_toolsets": ["set1"]
        }
        conditions = extract_skill_conditions(frontmatter)
        
        assert conditions["required_tools"] == ["tool1", "tool2"]
        assert conditions["required_toolsets"] == ["set1"]
    
    def test_missing_conditions(self):
        """Test with no conditions specified."""
        frontmatter = {"name": "test"}
        conditions = extract_skill_conditions(frontmatter)
        
        assert conditions["required_tools"] == []
        assert conditions["required_toolsets"] == []
    
    def test_empty_conditions(self):
        """Test with empty condition lists."""
        frontmatter = {
            "required_tools": [],
            "required_toolsets": []
        }
        conditions = extract_skill_conditions(frontmatter)
        
        assert conditions["required_tools"] == []
        assert conditions["required_toolsets"] == []


class TestValidateSkillName:
    """Tests for validate_skill_name function."""
    
    def test_valid_names(self):
        """Test valid skill names."""
        valid_names = [
            "python-debugging",
            "web-research",
            "log.analysis",
            "test_skill",
            "skill123",
            "a",
            "a" * 64,  # Max length
        ]
        for name in valid_names:
            error = validate_skill_name(name)
            assert error is None, f"Expected {name} to be valid, got error: {error}"
    
    def test_invalid_names(self):
        """Test invalid skill names."""
        invalid_names = [
            "",  # Empty
            "UPPERCASE",  # Uppercase
            "has spaces",  # Spaces
            "has/slash",  # Slash
            "has\\backslash",  # Backslash
            "../traversal",  # Directory traversal
            "a" * 65,  # Too long
            "special!char",  # Special character
        ]
        for name in invalid_names:
            error = validate_skill_name(name)
            assert error is not None, f"Expected {name} to be invalid"
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Max length exactly
        assert validate_skill_name("a" * 64) is None
        
        # One character over max
        assert validate_skill_name("a" * 65) is not None


class TestValidateSkillCategory:
    """Tests for validate_skill_category function."""
    
    def test_valid_categories(self):
        """Test valid category names."""
        valid_categories = [
            "development",
            "research",
            "system",
            "data-science",
            "web.scraping",
        ]
        for category in valid_categories:
            error = validate_skill_category(category)
            assert error is None, f"Expected {category} to be valid, got error: {error}"
    
    def test_none_category(self):
        """Test None category (allowed)."""
        error = validate_skill_category(None)
        assert error is None
    
    def test_invalid_categories(self):
        """Test invalid category names."""
        invalid_categories = [
            "UPPERCASE",
            "has spaces",
            "has/slash",
        ]
        for category in invalid_categories:
            error = validate_skill_category(category)
            assert error is not None, f"Expected {category} to be invalid"


class TestValidateSkillFrontmatter:
    """Tests for validate_skill_frontmatter function."""
    
    def test_valid_frontmatter(self):
        """Test valid frontmatter."""
        content = """---
name: test-skill
description: A test skill for validation
---

Body content
"""
        error = validate_skill_frontmatter(content)
        assert error is None
    
    def test_missing_name(self):
        """Test frontmatter missing name field."""
        content = """---
description: A test skill
---

Body
"""
        error = validate_skill_frontmatter(content)
        assert error is not None
        assert "name" in error.lower()
    
    def test_missing_description(self):
        """Test frontmatter missing description field."""
        content = """---
name: test-skill
---

Body
"""
        error = validate_skill_frontmatter(content)
        assert error is not None
        assert "description" in error.lower()
    
    def test_description_too_long(self):
        """Test frontmatter with description exceeding max length."""
        long_desc = "x" * 1100
        content = f"""---
name: test-skill
description: {long_desc}
---

Body
"""
        error = validate_skill_frontmatter(content, max_desc_length=1024)
        assert error is not None
        assert "description" in error.lower()
    
    def test_invalid_yaml(self):
        """Test invalid YAML frontmatter."""
        content = """---
name: test-skill
description: [unclosed list
---

Body
"""
        error = validate_skill_frontmatter(content)
        assert error is not None
    
    def test_no_frontmatter(self):
        """Test content with no frontmatter."""
        content = "Just some content without frontmatter"
        error = validate_skill_frontmatter(content)
        assert error is not None


class TestGetDisabledSkillNames:
    """Tests for get_disabled_skill_names function."""
    
    def test_with_disabled_skills(self):
        """Test with disabled skills in config."""
        config = {
            "skills": {
                "disabled": ["skill1", "skill2"]
            }
        }
        disabled = get_disabled_skill_names(config)
        assert disabled == {"skill1", "skill2"}
    
    def test_no_disabled_skills(self):
        """Test with no disabled skills."""
        config = {"skills": {}}
        disabled = get_disabled_skill_names(config)
        assert disabled == set()
    
    def test_no_skills_section(self):
        """Test with no skills section in config."""
        config = {}
        disabled = get_disabled_skill_names(config)
        assert disabled == set()
    
    def test_none_config(self):
        """Test with None config (uses actual config)."""
        # This will read from actual config file
        disabled = get_disabled_skill_names(None)
        assert isinstance(disabled, set)


class TestGetSkillsDirectory:
    """Tests for get_skills_directory function."""
    
    def test_returns_path(self):
        """Test that function returns a Path object."""
        skills_dir = get_skills_directory()
        assert isinstance(skills_dir, Path)
    
    def test_contains_dominusprime(self):
        """Test that path contains .dominusprime."""
        skills_dir = get_skills_directory()
        assert ".dominusprime" in str(skills_dir)
    
    def test_ends_with_skills(self):
        """Test that path ends with skills."""
        skills_dir = get_skills_directory()
        assert skills_dir.name == "skills"


class TestIterSkillFiles:
    """Tests for iter_skill_files function."""
    
    def test_empty_directory(self):
        """Test iteration over empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            files = list(iter_skill_files(skills_dir))
            assert files == []
    
    def test_with_skill_files(self):
        """Test iteration with skill files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            
            # Create skill directories
            skill1 = skills_dir / "category1" / "skill1"
            skill2 = skills_dir / "category2" / "skill2"
            skill1.mkdir(parents=True)
            skill2.mkdir(parents=True)
            
            # Create SKILL.md files
            (skill1 / "SKILL.md").write_text("skill 1")
            (skill2 / "SKILL.md").write_text("skill 2")
            
            files = list(iter_skill_files(skills_dir))
            assert len(files) == 2
            
            # Check sorted order
            assert files[0].parent.name == "skill1"
            assert files[1].parent.name == "skill2"
    
    def test_ignores_non_skill_files(self):
        """Test that non-SKILL.md files are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            
            # Create skill with SKILL.md and other files
            skill = skills_dir / "skill1"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("skill")
            (skill / "README.md").write_text("readme")
            (skill / "other.txt").write_text("other")
            
            files = list(iter_skill_files(skills_dir))
            assert len(files) == 1
            assert files[0].name == "SKILL.md"


class TestFindSkillByName:
    """Tests for find_skill_by_name function."""
    
    def test_find_existing_skill(self):
        """Test finding an existing skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            
            # Create skill
            skill_dir = skills_dir / "category" / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("test")
            
            # Find it
            found = find_skill_by_name("test-skill", skills_dir)
            assert found is not None
            assert found == skill_dir
    
    def test_find_nonexistent_skill(self):
        """Test finding a non-existent skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            
            found = find_skill_by_name("nonexistent", skills_dir)
            assert found is None
    
    def test_find_skill_without_category(self):
        """Test finding a skill without category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            
            # Create skill at top level
            skill_dir = skills_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("test")
            
            found = find_skill_by_name("test-skill", skills_dir)
            assert found is not None
            assert found == skill_dir


class TestBuildSkillPath:
    """Tests for build_skill_path function."""
    
    def test_with_category(self):
        """Test building path with category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            
            path = build_skill_path("test-skill", "development", skills_dir)
            
            assert path == skills_dir / "development" / "test-skill"
    
    def test_without_category(self):
        """Test building path without category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            
            path = build_skill_path("test-skill", None, skills_dir)
            
            assert path == skills_dir / "test-skill"
    
    def test_default_skills_dir(self):
        """Test building path with default skills directory."""
        path = build_skill_path("test-skill", "development")
        
        assert ".dominusprime" in str(path)
        assert "skills" in str(path)
        assert "development" in str(path)
        assert "test-skill" in str(path)


class TestGetSkillSubdirs:
    """Tests for get_skill_subdirs function."""
    
    def test_returns_set(self):
        """Test that function returns a set."""
        subdirs = get_skill_subdirs()
        assert isinstance(subdirs, set)
    
    def test_contains_expected_subdirs(self):
        """Test that set contains expected subdirectories."""
        subdirs = get_skill_subdirs()
        
        expected = {"references", "templates", "scripts", "assets"}
        assert subdirs == expected
    
    def test_immutability(self):
        """Test that returned set is independent."""
        subdirs1 = get_skill_subdirs()
        subdirs2 = get_skill_subdirs()
        
        subdirs1.add("custom")
        
        # subdirs2 should not be affected
        assert "custom" not in subdirs2
