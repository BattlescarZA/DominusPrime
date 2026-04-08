# -*- coding: utf-8 -*-
"""Unit tests for skill_manager tool."""
import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from dominusprime.agents.tools.skill_manager import skill_manage


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


class TestSkillManagerCreate:
    """Tests for skill_manage create action."""
    
    @pytest.mark.asyncio
    async def test_create_simple_skill(self, temp_skills_dir):
        """Test creating a simple skill."""
        content = """---
name: test-skill
description: A test skill
---

# Test Skill

This is a test skill.
"""
        
        result_str = await skill_manage(
            action="create",
            name="test-skill",
            content=content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert "test-skill" in result["message"]
        assert "path" in result
        
        # Verify file was created
        skill_file = temp_skills_dir / "test-skill" / "SKILL.md"
        assert skill_file.exists()
        assert skill_file.read_text() == content
    
    @pytest.mark.asyncio
    async def test_create_skill_with_category(self, temp_skills_dir):
        """Test creating a skill with category."""
        content = """---
name: test-skill
description: A test skill
---

Body
"""
        
        result_str = await skill_manage(
            action="create",
            name="test-skill",
            category="development",
            content=content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify file was created in category directory
        skill_file = temp_skills_dir / "development" / "test-skill" / "SKILL.md"
        assert skill_file.exists()
    
    @pytest.mark.asyncio
    async def test_create_duplicate_skill(self, temp_skills_dir):
        """Test creating a duplicate skill fails."""
        content = """---
name: test-skill
description: A test skill
---

Body
"""
        
        # Create first time
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Try to create again
        result_str = await skill_manage(action="create", name="test-skill", content=content)
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "already exists" in result["message"]
    
    @pytest.mark.asyncio
    async def test_create_invalid_name(self, temp_skills_dir):
        """Test creating skill with invalid name fails."""
        content = """---
name: TEST-SKILL
description: Invalid name
---

Body
"""
        
        result_str = await skill_manage(
            action="create",
            name="INVALID NAME",  # Uppercase and spaces
            content=content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "invalid" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_missing_frontmatter(self, temp_skills_dir):
        """Test creating skill without required frontmatter fails."""
        content = """---
name: test-skill
---

Body
"""  # Missing description
        
        result_str = await skill_manage(
            action="create",
            name="test-skill",
            content=content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "description" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_with_dangerous_content(self, temp_skills_dir):
        """Test that security scanning blocks dangerous content."""
        content = """---
name: dangerous-skill
description: A dangerous skill
---

# Dangerous Skill

```python
import subprocess
subprocess.run(["rm", "-rf", "/"])
```
"""
        
        result_str = await skill_manage(
            action="create",
            name="dangerous-skill",
            content=content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "security" in result["message"].lower()


class TestSkillManagerEdit:
    """Tests for skill_manage edit action."""
    
    @pytest.mark.asyncio
    async def test_edit_existing_skill(self, temp_skills_dir):
        """Test editing an existing skill."""
        # Create skill
        original_content = """---
name: test-skill
description: Original description
---

Original body
"""
        await skill_manage(action="create", name="test-skill", content=original_content)
        
        # Edit skill
        new_content = """---
name: test-skill
description: Updated description
---

Updated body
"""
        result_str = await skill_manage(
            action="edit",
            name="test-skill",
            content=new_content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify content was updated
        skill_file = temp_skills_dir / "test-skill" / "SKILL.md"
        assert skill_file.read_text() == new_content
    
    @pytest.mark.asyncio
    async def test_edit_nonexistent_skill(self, temp_skills_dir):
        """Test editing a nonexistent skill fails."""
        content = """---
name: test-skill
description: Test
---

Body
"""
        
        result_str = await skill_manage(
            action="edit",
            name="nonexistent",
            content=content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_edit_with_invalid_frontmatter(self, temp_skills_dir):
        """Test editing with invalid frontmatter fails."""
        # Create skill
        original_content = """---
name: test-skill
description: Original
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=original_content)
        
        # Try to edit with invalid frontmatter
        invalid_content = """---
name: test-skill
---

Body
"""  # Missing description
        
        result_str = await skill_manage(
            action="edit",
            name="test-skill",
            content=invalid_content,
        )
        result = json.loads(result_str)
        
        assert result["success"] is False


class TestSkillManagerPatch:
    """Tests for skill_manage patch action."""
    
    @pytest.mark.asyncio
    async def test_patch_literal_replacement(self, temp_skills_dir):
        """Test literal text replacement."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

# Test Skill

Original text here.
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Patch it
        result_str = await skill_manage(
            action="patch",
            name="test-skill",
            find="Original text",
            replace="Updated text",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["matches"] == 1
        
        # Verify content was updated
        skill_file = temp_skills_dir / "test-skill" / "SKILL.md"
        new_content = skill_file.read_text()
        assert "Updated text" in new_content
        assert "Original text" not in new_content
    
    @pytest.mark.asyncio
    async def test_patch_regex_replacement(self, temp_skills_dir):
        """Test regex text replacement."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Version 1.0.0
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Patch with regex
        result_str = await skill_manage(
            action="patch",
            name="test-skill",
            find="regex:Version \\d+\\.\\d+\\.\\d+",
            replace="Version 2.0.0",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        assert result["matches"] == 1
        
        # Verify content
        skill_file = temp_skills_dir / "test-skill" / "SKILL.md"
        new_content = skill_file.read_text()
        assert "Version 2.0.0" in new_content
    
    @pytest.mark.asyncio
    async def test_patch_no_match(self, temp_skills_dir):
        """Test patch with no matches fails."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Some content
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Try to patch non-existent text
        result_str = await skill_manage(
            action="patch",
            name="test-skill",
            find="nonexistent",
            replace="replacement",
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_patch_supporting_file(self, temp_skills_dir):
        """Test patching a supporting file."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Add a supporting file
        await skill_manage(
            action="write_file",
            name="test-skill",
            file_path="references/notes.md",
            content="Original notes",
        )
        
        # Patch the supporting file
        result_str = await skill_manage(
            action="patch",
            name="test-skill",
            file_path="references/notes.md",
            find="Original",
            replace="Updated",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify file was updated
        ref_file = temp_skills_dir / "test-skill" / "references" / "notes.md"
        assert ref_file.read_text() == "Updated notes"


class TestSkillManagerDelete:
    """Tests for skill_manage delete action."""
    
    @pytest.mark.asyncio
    async def test_delete_existing_skill(self, temp_skills_dir):
        """Test deleting an existing skill."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Verify it exists
        skill_dir = temp_skills_dir / "test-skill"
        assert skill_dir.exists()
        
        # Delete it
        result_str = await skill_manage(action="delete", name="test-skill")
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify it's gone
        assert not skill_dir.exists()
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_skill(self, temp_skills_dir):
        """Test deleting a nonexistent skill fails."""
        result_str = await skill_manage(action="delete", name="nonexistent")
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()


class TestSkillManagerWriteFile:
    """Tests for skill_manage write_file action."""
    
    @pytest.mark.asyncio
    async def test_write_reference_file(self, temp_skills_dir):
        """Test writing a reference file."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Write reference file
        result_str = await skill_manage(
            action="write_file",
            name="test-skill",
            file_path="references/guide.md",
            content="# Reference Guide\n\nSome content",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify file was created
        ref_file = temp_skills_dir / "test-skill" / "references" / "guide.md"
        assert ref_file.exists()
        assert "Reference Guide" in ref_file.read_text()
    
    @pytest.mark.asyncio
    async def test_write_template_file(self, temp_skills_dir):
        """Test writing a template file."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Write template
        result_str = await skill_manage(
            action="write_file",
            name="test-skill",
            file_path="templates/example.txt",
            content="Template content",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify file
        template_file = temp_skills_dir / "test-skill" / "templates" / "example.txt"
        assert template_file.exists()
    
    @pytest.mark.asyncio
    async def test_write_file_invalid_path(self, temp_skills_dir):
        """Test writing file with invalid path fails."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Try to write file outside allowed directories
        result_str = await skill_manage(
            action="write_file",
            name="test-skill",
            file_path="invalid/file.txt",
            content="content",
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "invalid" in result["message"].lower() or "must be in" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_overwrite_existing_file(self, temp_skills_dir):
        """Test overwriting an existing supporting file."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Write file
        await skill_manage(
            action="write_file",
            name="test-skill",
            file_path="references/notes.md",
            content="Original content",
        )
        
        # Overwrite it
        result_str = await skill_manage(
            action="write_file",
            name="test-skill",
            file_path="references/notes.md",
            content="New content",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify content was updated
        ref_file = temp_skills_dir / "test-skill" / "references" / "notes.md"
        assert ref_file.read_text() == "New content"


class TestSkillManagerRemoveFile:
    """Tests for skill_manage remove_file action."""
    
    @pytest.mark.asyncio
    async def test_remove_supporting_file(self, temp_skills_dir):
        """Test removing a supporting file."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Add a file
        await skill_manage(
            action="write_file",
            name="test-skill",
            file_path="references/notes.md",
            content="Notes",
        )
        
        # Verify it exists
        ref_file = temp_skills_dir / "test-skill" / "references" / "notes.md"
        assert ref_file.exists()
        
        # Remove it
        result_str = await skill_manage(
            action="remove_file",
            name="test-skill",
            file_path="references/notes.md",
        )
        result = json.loads(result_str)
        
        assert result["success"] is True
        
        # Verify it's gone
        assert not ref_file.exists()
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_file(self, temp_skills_dir):
        """Test removing a nonexistent file fails."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Try to remove nonexistent file
        result_str = await skill_manage(
            action="remove_file",
            name="test-skill",
            file_path="references/nonexistent.md",
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_cannot_remove_skill_md(self, temp_skills_dir):
        """Test that SKILL.md cannot be removed via remove_file."""
        # Create skill
        content = """---
name: test-skill
description: Test skill
---

Body
"""
        await skill_manage(action="create", name="test-skill", content=content)
        
        # Try to remove SKILL.md
        result_str = await skill_manage(
            action="remove_file",
            name="test-skill",
            file_path="SKILL.md",
        )
        result = json.loads(result_str)
        
        assert result["success"] is False


class TestSkillManagerInvalidAction:
    """Tests for invalid actions."""
    
    @pytest.mark.asyncio
    async def test_invalid_action(self, temp_skills_dir):
        """Test that invalid action fails."""
        result_str = await skill_manage(
            action="invalid_action",
            name="test-skill",
        )
        result = json.loads(result_str)
        
        assert result["success"] is False
        assert "invalid" in result["message"].lower()
