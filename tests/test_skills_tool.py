# -*- coding: utf-8 -*-
"""Unit tests for skills_tool (discovery tool)."""
import json
import tempfile
from pathlib import Path

import pytest

from dominusprime.agents.tools.skill_manager import skill_manage
from dominusprime.agents.tools.skills_tool import skills


@pytest.fixture
def temp_skills_dir(monkeypatch):
    """Create a temporary skills directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()
        
        # Mock get_skills_directory to return our temp directory
        from dominusprime.agents.utils import skill_utils
        monkeypatch.setattr(
            skill_utils,
            "get_skills_directory",
            lambda: skills_dir
        )
        
        yield skills_dir


@pytest.fixture
async def populated_skills_dir(temp_skills_dir):
    """Create a skills directory with some test skills."""
    # Create skill 1
    await skill_manage(
        action="create",
        name="python-debugging",
        category="development",
        content="""---
name: python-debugging
description: Debug Python applications
platforms: [linux, macos, windows]
required_tools: [execute_shell_command]
tags: [python, debugging]
---

# Python Debugging

Debug Python code using pdb.
"""
    )
    
    # Create skill 2
    await skill_manage(
        action="create",
        name="web-research",
        category="research",
        content="""---
name: web-research
description: Conduct effective web research
platforms: [linux, macos, windows]
required_tools: [browser_use]
tags: [research, web]
---

# Web Research

Search and analyze web content.
"""
    )
    
    # Create skill 3 (no category)
    await skill_manage(
        action="create",
        name="general-skill",
        content="""---
name: general-skill
description: A general purpose skill
---

# General Skill

General purpose content.
"""
    )
    
    return temp_skills_dir


class TestSkillsToolList:
    """Tests for skills list action."""
    
    @pytest.mark.asyncio
    async def test_list_empty_directory(self, temp_skills_dir):
        """Test listing skills in empty directory."""
        result_str = await skills(action="list")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] == 0
        assert result["skills"] == []
    
    @pytest.mark.asyncio
    async def test_list_all_skills(self, populated_skills_dir):
        """Test listing all skills."""
        result_str = await skills(action="list")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["skills"]) == 3
        
        # Check skill names
        skill_names = {s["name"] for s in result["skills"]}
        assert skill_names == {"python-debugging", "web-research", "general-skill"}
    
    @pytest.mark.asyncio
    async def test_list_by_category(self, populated_skills_dir):
        """Test filtering skills by category."""
        result_str = await skills(action="list", category="development")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] == 1
        assert result["skills"][0]["name"] == "python-debugging"
        assert result["skills"][0]["category"] == "development"
    
    @pytest.mark.asyncio
    async def test_list_includes_metadata(self, populated_skills_dir):
        """Test that list includes skill metadata."""
        result_str = await skills(action="list")
        result = json.loads(result_str)
        
        skill = result["skills"][0]
        
        # Check metadata fields
        assert "name" in skill
        assert "category" in skill
        assert "description" in skill
        assert "platforms" in skill
        assert "required_tools" in skill
        assert "required_toolsets" in skill
        assert "path" in skill
        assert "disabled" in skill
    
    @pytest.mark.asyncio
    async def test_list_with_disabled_skills(self, populated_skills_dir, monkeypatch):
        """Test listing includes disabled skills when requested."""
        # Mock get_disabled_skill_names to return python-debugging as disabled
        from dominusprime.agents.utils import skill_utils
        monkeypatch.setattr(
            skill_utils,
            "get_disabled_skill_names",
            lambda config=None: {"python-debugging"}
        )
        
        # List without disabled
        result_str = await skills(action="list", include_disabled=False)
        result = json.loads(result_str)
        assert result["count"] == 2  # Should exclude python-debugging
        
        # List with disabled
        result_str = await skills(action="list", include_disabled=True)
        result = json.loads(result_str)
        assert result["count"] == 3  # Should include all
        
        # Check that python-debugging is marked as disabled
        python_skill = next(s for s in result["skills"] if s["name"] == "python-debugging")
        assert python_skill["disabled"] is True


class TestSkillsToolView:
    """Tests for skills view action."""
    
    @pytest.mark.asyncio
    async def test_view_existing_skill(self, populated_skills_dir):
        """Test viewing an existing skill."""
        result_str = await skills(action="view", name="python-debugging")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["name"] == "python-debugging"
        assert result["category"] == "development"
        assert "content" in result
        assert "frontmatter" in result
        assert "body" in result
        
        # Check frontmatter
        assert result["frontmatter"]["name"] == "python-debugging"
        assert result["frontmatter"]["description"] == "Debug Python applications"
        
        # Check body
        assert "Python Debugging" in result["body"]
    
    @pytest.mark.asyncio
    async def test_view_nonexistent_skill(self, populated_skills_dir):
        """Test viewing a nonexistent skill fails."""
        result_str = await skills(action="view", name="nonexistent")
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_view_skill_without_category(self, populated_skills_dir):
        """Test viewing a skill without category."""
        result_str = await skills(action="view", name="general-skill")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["name"] == "general-skill"
        assert result["category"] is None
    
    @pytest.mark.asyncio
    async def test_view_with_supporting_files(self, populated_skills_dir):
        """Test viewing skill with supporting files."""
        # Add a supporting file
        await skill_manage(
            action="write_file",
            name="python-debugging",
            file_path="references/pdb-guide.md",
            content="# PDB Guide\n\nSome pdb info",
        )
        
        # View without supporting files
        result_str = await skills(
            action="view",
            name="python-debugging",
            include_supporting_files=False,
        )
        result = json.loads(result_str)
        assert "supporting_files" not in result
        
        # View with supporting files
        result_str = await skills(
            action="view",
            name="python-debugging",
            include_supporting_files=True,
        )
        result = json.loads(result_str)
        
        assert "supporting_files" in result
        assert len(result["supporting_files"]) == 1
        
        file_info = result["supporting_files"][0]
        assert file_info["path"] == "references/pdb-guide.md"
        assert "PDB Guide" in file_info["content"]
        assert file_info["size"] > 0


class TestSkillsToolSearch:
    """Tests for skills search action."""
    
    @pytest.mark.asyncio
    async def test_search_by_name(self, populated_skills_dir):
        """Test searching skills by name."""
        result_str = await skills(action="search", query="python")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] == 1
        assert result["results"][0]["name"] == "python-debugging"
        assert result["results"][0]["match_type"] == "metadata"
    
    @pytest.mark.asyncio
    async def test_search_by_description(self, populated_skills_dir):
        """Test searching skills by description."""
        result_str = await skills(action="search", query="research")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] >= 1
        
        # Should find web-research
        names = {r["name"] for r in result["results"]}
        assert "web-research" in names
    
    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, populated_skills_dir):
        """Test that search is case-insensitive."""
        result_str = await skills(action="search", query="PYTHON")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] >= 1
        assert any(r["name"] == "python-debugging" for r in result["results"])
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, populated_skills_dir):
        """Test search with no results."""
        result_str = await skills(action="search", query="nonexistent-term-xyz")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] == 0
        assert result["results"] == []
    
    @pytest.mark.asyncio
    async def test_search_in_content(self, populated_skills_dir):
        """Test searching in skill body content."""
        # Search without content search
        result_str = await skills(
            action="search",
            query="pdb",
            search_content=False,
        )
        result = json.loads(result_str)
        # Should not find it (not in name or description)
        assert result["count"] == 0
        
        # Search with content search
        result_str = await skills(
            action="search",
            query="pdb",
            search_content=True,
        )
        result = json.loads(result_str)
        
        # Should find it (in body content)
        assert result["count"] >= 1
        skill = next(r for r in result["results"] if r["name"] == "python-debugging")
        assert skill["match_type"] == "content"
    
    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, populated_skills_dir):
        """Test searching with category filter."""
        result_str = await skills(
            action="search",
            query="debug",
            category="development",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        # Should only search in development category
        for skill in result["results"]:
            assert skill["category"] == "development"


class TestSkillsToolCategories:
    """Tests for skills categories action."""
    
    @pytest.mark.asyncio
    async def test_get_categories(self, populated_skills_dir):
        """Test getting list of categories."""
        result_str = await skills(action="categories")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] == 2
        assert set(result["categories"]) == {"development", "research"}
    
    @pytest.mark.asyncio
    async def test_categories_sorted(self, populated_skills_dir):
        """Test that categories are sorted."""
        result_str = await skills(action="categories")
        result = json.loads(result_str)
        
        categories = result["categories"]
        assert categories == sorted(categories)
    
    @pytest.mark.asyncio
    async def test_categories_empty_directory(self, temp_skills_dir):
        """Test categories in empty directory."""
        result_str = await skills(action="categories")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["count"] == 0
        assert result["categories"] == []


class TestSkillsToolInvalidAction:
    """Tests for invalid actions."""
    
    @pytest.mark.asyncio
    async def test_invalid_action(self, temp_skills_dir):
        """Test that invalid action fails."""
        result_str = await skills(action="invalid_action")
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "invalid" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_view_missing_name(self, temp_skills_dir):
        """Test view action without name parameter."""
        result_str = await skills(action="view")
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "name" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_search_missing_query(self, temp_skills_dir):
        """Test search action without query parameter."""
        result_str = await skills(action="search")
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "query" in result["message"].lower()


class TestSkillsToolIntegration:
    """Integration tests combining multiple operations."""
    
    @pytest.mark.asyncio
    async def test_create_then_list(self, temp_skills_dir):
        """Test creating a skill and then listing it."""
        # Create skill
        await skill_manage(
            action="create",
            name="test-skill",
            content="""---
name: test-skill
description: Test skill
---

Body
"""
        )
        
        # List skills
        result_str = await skills(action="list")
        result = json.loads(result_str)
        
        assert result["count"] == 1
        assert result["skills"][0]["name"] == "test-skill"
    
    @pytest.mark.asyncio
    async def test_create_then_view(self, temp_skills_dir):
        """Test creating a skill and then viewing it."""
        content = """---
name: test-skill
description: Test skill for viewing
---

# Test Content

This is test content.
"""
        
        # Create skill
        await skill_manage(
            action="create",
            name="test-skill",
            content=content,
        )
        
        # View skill
        result_str = await skills(action="view", name="test-skill")
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["content"] == content
        assert "Test Content" in result["body"]
    
    @pytest.mark.asyncio
    async def test_create_then_search(self, temp_skills_dir):
        """Test creating a skill and then searching for it."""
        # Create skill
        await skill_manage(
            action="create",
            name="searchable-skill",
            content="""---
name: searchable-skill
description: A skill to search for
---

Unique search term: TESTXYZ123
"""
        )
        
        # Search for it
        result_str = await skills(action="search", query="searchable")
        result = json.loads(result_str)
        
        assert result["count"] == 1
        assert result["results"][0]["name"] == "searchable-skill"
        
        # Search in content
        result_str = await skills(
            action="search",
            query="TESTXYZ123",
            search_content=True,
        )
        result = json.loads(result_str)
        
        assert result["count"] == 1
        assert result["results"][0]["match_type"] == "content"
