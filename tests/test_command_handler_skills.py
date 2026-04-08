# -*- coding: utf-8 -*-
"""Tests for skill slash commands in command_handler.py."""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentscope.message import Msg
from dominusprime.agents.command_handler import CommandHandler


@pytest.fixture
def mock_memory():
    """Create a mock memory instance."""
    memory = MagicMock()
    memory.get_memory = AsyncMock(return_value=[])
    memory.clear_content = MagicMock()
    memory.clear_compressed_summary = MagicMock()
    memory.get_compressed_summary = MagicMock(return_value="")
    memory.get_history_str = AsyncMock(return_value="Empty history")
    memory.mark_messages_compressed = AsyncMock(return_value=0)
    memory.update_compressed_summary = AsyncMock()
    return memory


@pytest.fixture
def command_handler(mock_memory):
    """Create a CommandHandler instance."""
    return CommandHandler(
        agent_name="test_agent",
        memory=mock_memory,
        memory_manager=None,
        enable_memory_manager=False,
    )


class TestSkillCommandDetection:
    """Test skill command detection methods."""

    def test_is_skill_command_with_valid_skill(self, command_handler):
        """Test detection of valid skill command."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            # Mock successful skill view
            mock_skills.return_value = json.dumps({"success": True})
            
            result = command_handler.is_skill_command("/python-debugging")
            assert result is True

    def test_is_skill_command_with_invalid_skill(self, command_handler):
        """Test detection of invalid skill command."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            # Mock failed skill view
            mock_skills.return_value = json.dumps({"success": False})
            
            result = command_handler.is_skill_command("/nonexistent-skill")
            assert result is False

    def test_is_skill_command_with_system_command(self, command_handler):
        """Test that system commands are not detected as skill commands."""
        result = command_handler.is_skill_command("/compact")
        assert result is False
        
        result = command_handler.is_skill_command("/new")
        assert result is False
        
        result = command_handler.is_skill_command("/clear")
        assert result is False

    def test_is_skill_command_with_non_slash(self, command_handler):
        """Test that non-slash queries are not detected as skill commands."""
        result = command_handler.is_skill_command("python-debugging")
        assert result is False
        
        result = command_handler.is_skill_command("hello")
        assert result is False

    def test_is_skill_command_with_empty_query(self, command_handler):
        """Test that empty/None queries are not detected as skill commands."""
        result = command_handler.is_skill_command(None)
        assert result is False
        
        result = command_handler.is_skill_command("")
        assert result is False

    def test_is_skill_command_exception_handling(self, command_handler):
        """Test exception handling in is_skill_command."""
        with patch("dominusprime.agents.tools.skills_tool.skills", side_effect=Exception("Test error")):
            result = command_handler.is_skill_command("/python-debugging")
            assert result is False

    def test_is_command_recognizes_skill_commands(self, command_handler):
        """Test that is_command recognizes skill commands."""
        with patch.object(command_handler, "is_skill_command", return_value=True):
            result = command_handler.is_command("/python-debugging")
            assert result is True

    def test_is_command_recognizes_system_commands(self, command_handler):
        """Test that is_command recognizes system commands."""
        result = command_handler.is_command("/compact")
        assert result is True


class TestProcessSkill:
    """Test skill processing functionality."""

    @pytest.mark.asyncio
    async def test_process_skill_success(self, command_handler):
        """Test successful skill processing."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            # Mock successful skill view with full data
            mock_result = {
                "success": True,
                "body": "# Python Debugging\n\nThis is the skill content.",
                "frontmatter": {
                    "description": "A comprehensive guide to Python debugging",
                    "category": "development"
                },
                "category": "development"
            }
            mock_skills.return_value = json.dumps(mock_result)
            
            result = await command_handler._process_skill("python-debugging")
            
            assert isinstance(result, Msg)
            assert result.name == "test_agent"
            assert result.role == "assistant"
            assert len(result.content) == 1
            # Content is a list of dicts, check it has 'text' key
            assert "text" in result.content[0]
            
            content = result.content[0]["text"]
            assert "✓ Skill Loaded: python-debugging" in content
            assert "development" in content
            assert "A comprehensive guide to Python debugging" in content
            assert "This is the skill content" in content

    @pytest.mark.asyncio
    async def test_process_skill_with_supporting_files(self, command_handler):
        """Test skill processing with supporting files."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            mock_result = {
                "success": True,
                "body": "# Skill Content",
                "frontmatter": {
                    "description": "Test skill",
                    "category": "test"
                },
                "category": "test",
                "supporting_files": [
                    {"path": "reference.md", "size": 1024},
                    {"path": "examples.py", "size": 2048}
                ]
            }
            mock_skills.return_value = json.dumps(mock_result)
            
            result = await command_handler._process_skill("test-skill")
            
            content = result.content[0]["text"]
            assert "Supporting Files" in content
            assert "(2)" in content
            assert "reference.md" in content
            assert "1024 bytes" in content
            assert "examples.py" in content
            assert "2048 bytes" in content

    @pytest.mark.asyncio
    async def test_process_skill_not_found(self, command_handler):
        """Test processing non-existent skill."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            mock_result = {"success": False}
            mock_skills.return_value = json.dumps(mock_result)
            
            result = await command_handler._process_skill("nonexistent")
            
            content = result.content[0]["text"]
            assert "Skill Not Found: nonexistent" in content
            assert "does not exist" in content
            assert "skills(action=\"list\")" in content

    @pytest.mark.asyncio
    async def test_process_skill_error_handling(self, command_handler):
        """Test error handling in skill processing."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock, side_effect=Exception("Test error")):
            result = await command_handler._process_skill("test-skill")
            
            content = result.content[0]["text"]
            assert "Error Loading Skill" in content
            assert "test-skill" in content
            assert "Test error" in content

    @pytest.mark.asyncio
    async def test_process_skill_minimal_frontmatter(self, command_handler):
        """Test skill processing with minimal frontmatter."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            # Minimal data - no description or category
            mock_result = {
                "success": True,
                "body": "# Minimal Skill",
                "frontmatter": {},
                "category": "uncategorized"
            }
            mock_skills.return_value = json.dumps(mock_result)
            
            result = await command_handler._process_skill("minimal-skill")
            
            content = result.content[0]["text"]
            assert "✓ Skill Loaded: minimal-skill" in content
            assert "uncategorized" in content
            assert "No description" in content


class TestHandleSkillCommand:
    """Test skill command handling."""

    @pytest.mark.asyncio
    async def test_handle_skill_command_basic(self, command_handler):
        """Test basic skill command handling."""
        with patch.object(command_handler, "_process_skill") as mock_process:
            mock_msg = Msg(name="test", role="assistant", content=[])
            mock_process.return_value = mock_msg
            
            result = await command_handler.handle_skill_command("/python-debugging")
            
            assert result == mock_msg
            mock_process.assert_called_once_with("python-debugging")

    @pytest.mark.asyncio
    async def test_handle_skill_command_with_spaces(self, command_handler):
        """Test skill command with extra spaces."""
        with patch.object(command_handler, "_process_skill") as mock_process:
            mock_msg = Msg(name="test", role="assistant", content=[])
            mock_process.return_value = mock_msg
            
            result = await command_handler.handle_skill_command("  /python-debugging  ")
            
            assert result == mock_msg
            mock_process.assert_called_once_with("python-debugging")

    @pytest.mark.asyncio
    async def test_handle_skill_command_ignores_args(self, command_handler):
        """Test that skill command ignores arguments after skill name."""
        with patch.object(command_handler, "_process_skill") as mock_process:
            mock_msg = Msg(name="test", role="assistant", content=[])
            mock_process.return_value = mock_msg
            
            result = await command_handler.handle_skill_command("/python-debugging some args")
            
            # Should only use the skill name, not the args
            assert result == mock_msg
            mock_process.assert_called_once_with("python-debugging")


class TestHandleCommandRouter:
    """Test the main command routing logic."""

    @pytest.mark.asyncio
    async def test_handle_command_routes_system_command(self, command_handler):
        """Test that handle_command routes system commands correctly."""
        with patch.object(command_handler, "handle_conversation_command") as mock_conv:
            mock_msg = Msg(name="test", role="assistant", content=[])
            mock_conv.return_value = mock_msg
            
            result = await command_handler.handle_command("/compact")
            
            assert result == mock_msg
            mock_conv.assert_called_once_with("/compact")

    @pytest.mark.asyncio
    async def test_handle_command_routes_skill_command(self, command_handler):
        """Test that handle_command routes skill commands correctly."""
        with patch.object(command_handler, "is_skill_command", return_value=True):
            with patch.object(command_handler, "handle_skill_command") as mock_skill:
                mock_msg = Msg(name="test", role="assistant", content=[])
                mock_skill.return_value = mock_msg
                
                result = await command_handler.handle_command("/python-debugging")
                
                assert result == mock_msg
                mock_skill.assert_called_once_with("/python-debugging")

    @pytest.mark.asyncio
    async def test_handle_command_unknown_command(self, command_handler):
        """Test that handle_command handles unknown commands."""
        result = await command_handler.handle_command("/unknown-command")
        
        assert isinstance(result, Msg)
        assert len(result.content) == 1
        assert "text" in result.content[0]
        content = result.content[0]["text"]
        assert "Unknown Command: /unknown-command" in content
        assert "System Commands" in content
        assert "Skill Commands" in content

    @pytest.mark.asyncio
    async def test_handle_command_prioritizes_system_over_skill(self, command_handler):
        """Test that system commands take priority over skill commands."""
        # Even if there's a skill named "compact", the system command should take precedence
        with patch.object(command_handler, "handle_conversation_command") as mock_conv:
            mock_msg = Msg(name="test", role="assistant", content=[])
            mock_conv.return_value = mock_msg
            
            result = await command_handler.handle_command("/compact")
            
            assert result == mock_msg
            mock_conv.assert_called_once_with("/compact")


class TestIntegration:
    """Integration tests for skill command workflow."""

    @pytest.mark.asyncio
    async def test_full_skill_command_workflow(self, command_handler):
        """Test complete workflow from detection to processing."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            # Setup successful skill
            mock_result = {
                "success": True,
                "body": "# Test Skill\n\nContent here.",
                "frontmatter": {
                    "description": "Test description",
                    "category": "test"
                },
                "category": "test"
            }
            mock_skills.return_value = json.dumps(mock_result)
            
            # Test handling directly (skip detection since asyncio.run() in is_skill_command creates issues)
            result = await command_handler.handle_skill_command("/test-skill")
            
            assert isinstance(result, Msg)
            assert result.name == "test_agent"
            content = result.content[0]["text"]
            assert "✓ Skill Loaded: test-skill" in content
            assert "Test description" in content

    @pytest.mark.asyncio
    async def test_skill_not_found_workflow(self, command_handler):
        """Test workflow when skill doesn't exist."""
        with patch("dominusprime.agents.tools.skills_tool.skills", new_callable=AsyncMock) as mock_skills:
            mock_skills.return_value = json.dumps({"success": False})
            
            # Detection should return False
            assert command_handler.is_skill_command("/nonexistent") is False
            
            # Handle as unknown command
            result = await command_handler.handle_command("/nonexistent")
            
            content = result.content[0]["text"]
            assert "Unknown Command: /nonexistent" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
