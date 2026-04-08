# -*- coding: utf-8 -*-
"""Integration tests for the complete skill auto-generation workflow.

This module tests the end-to-end functionality of:
- Trajectory tracking
- Pattern detection
- Template generation
- Approval workflow
- Full auto-generation manager
"""
import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from dominusprime.agents.utils.trajectory_tracker import (
    TrajectoryTracker,
    Trajectory,
    ToolCall,
)
from dominusprime.agents.utils.skill_template_generator import SkillTemplateGenerator
from dominusprime.agents.utils.skill_approval import SkillApprovalWorkflow
from dominusprime.agents.utils.skill_autogen_manager import SkillAutoGenManager


class TestEndToEndWorkflow:
    """Test complete workflow from task start to skill generation."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_simple_debugging_workflow(self, temp_storage):
        """Test complete workflow for a debugging task."""
        # Initialize manager
        manager = SkillAutoGenManager(
            storage_dir=temp_storage,
            auto_approve=True,  # Skip interactive approval for testing
            min_tools=3,
        )

        # Simulate debugging workflow
        manager.start_task("Debug Python application error")

        # Record typical debugging tool calls
        manager.record_tool(
            "execute_shell_command",
            {"command": "python app.py", "timeout": 30},
            {"stdout": "Traceback...", "stderr": "ImportError", "returncode": 1},
            success=False,
        )

        manager.record_tool(
            "read_file",
            {"path": "app.py", "mode": "slice"},
            {"content": "import nonexistent_module\n..."},
            success=True,
        )

        manager.record_tool(
            "search_files",
            {"path": ".", "regex": "import.*", "file_pattern": "*.py"},
            {"matches": [{"file": "app.py", "line": 1}]},
            success=True,
        )

        manager.record_tool(
            "write_to_file",
            {"path": "app.py", "content": "# Fixed imports\n..."},
            {"success": True},
            success=True,
        )

        manager.record_tool(
            "execute_shell_command",
            {"command": "python app.py", "timeout": 30},
            {"stdout": "Success!", "stderr": "", "returncode": 0},
            success=True,
        )

        # Complete task (synchronous test)
        result = asyncio.run(
            manager.complete_task(
                success=True, outcome="Fixed import error and application runs successfully"
            )
        )

        # Verify skill was generated
        assert result is not None, "Expected skill to be generated"
        assert result["name"]
        assert result["category"]
        assert result["content"]

        # Check content structure
        content = result["content"]
        assert "---" in content  # YAML frontmatter
        assert "name:" in content
        assert "description:" in content
        assert "## Steps" in content or "## Procedure" in content
        assert "execute_shell_command" in content
        assert "read_file" in content

        # Verify skill was saved
        category_dir = temp_storage / result["category"]
        skill_dir = category_dir / result["name"]
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"Skill file should be created at {skill_file}"

        # Read and validate saved content
        saved_content = skill_file.read_text(encoding="utf-8")
        assert saved_content == content

    @pytest.mark.asyncio
    async def test_research_workflow(self, temp_storage):
        """Test workflow for a research task."""
        manager = SkillAutoGenManager(
            storage_dir=temp_storage, auto_approve=True, min_tools=3
        )

        manager.start_task("Research machine learning frameworks")

        # Simulate research tool calls (5 to ensure skill-worthiness)
        manager.record_tool(
            "search_files",
            {"path": "docs", "regex": "tensorflow|pytorch", "file_pattern": "*.md"},
            {"matches": [{"file": "ml.md", "line": 10}]},
            success=True,
        )

        manager.record_tool(
            "read_file",
            {"path": "docs/ml.md", "mode": "slice"},
            {"content": "# Machine Learning\n\nFrameworks..."},
            success=True,
        )

        manager.record_tool(
            "execute_shell_command",
            {"command": "pip list | grep torch", "timeout": 10},
            {"stdout": "torch==2.0.0", "returncode": 0},
            success=True,
        )

        manager.record_tool(
            "read_file",
            {"path": "docs/pytorch.md", "mode": "slice"},
            {"content": "# PyTorch\n\n..."},
            success=True,
        )

        manager.record_tool(
            "write_to_file",
            {"path": "research_notes.md", "content": "# Research Summary\n..."},
            {"success": True},
            success=True,
        )

        result = await manager.complete_task(
            success=True, outcome="Compiled comprehensive framework comparison"
        )

        assert result is not None
        # Category inferred from tools (search_files has "file" so could be development)
        assert result["category"] in ["research", "development"]

    def test_insufficient_tools_no_generation(self, temp_storage):
        """Test that skills are not generated for simple tasks."""
        manager = SkillAutoGenManager(
            storage_dir=temp_storage, auto_approve=True, min_tools=3
        )

        manager.start_task("Simple file read")

        # Only 2 tool calls (below minimum)
        manager.record_tool(
            "read_file",
            {"path": "test.txt", "mode": "slice"},
            {"content": "Hello"},
            success=True,
        )

        manager.record_tool(
            "write_to_file",
            {"path": "output.txt", "content": "World"},
            {"success": True},
            success=True,
        )

        result = asyncio.run(
            manager.complete_task(success=True, outcome="Copied file content")
        )

        # Should not generate skill (insufficient complexity)
        assert result is None

    @pytest.mark.asyncio
    async def test_failed_task_no_generation(self, temp_storage):
        """Test that failed tasks don't generate skills."""
        manager = SkillAutoGenManager(
            storage_dir=temp_storage, auto_approve=True, min_tools=3
        )

        manager.start_task("Failing task")

        manager.record_tool("read_file", {"path": "missing.txt"}, None, success=False)
        manager.record_tool("read_file", {"path": "missing.txt"}, None, success=False)
        manager.record_tool("read_file", {"path": "missing.txt"}, None, success=False)

        result = await manager.complete_task(success=False, outcome="Task failed")

        # Failed tasks should not generate skills
        assert result is None

    @pytest.mark.asyncio
    async def test_rejection_workflow(self, temp_storage):
        """Test approval workflow with rejection."""
        manager = SkillAutoGenManager(
            storage_dir=temp_storage,
            auto_approve=False,  # Manual approval
            min_tools=3,
        )

        manager.start_task("Test task")

        # Record sufficient tool calls
        for i in range(4):
            manager.record_tool(
                "execute_shell_command",
                {"command": f"echo {i}"},
                {"stdout": str(i)},
                success=True,
            )

        # Mock rejection
        async def reject_callback(proposal: str) -> Dict[str, Any]:
            return {"approved": False}

        manager.workflow.propose_skill = AsyncMock(return_value=None)

        result = await manager.complete_task(success=True, outcome="Test completed")

        # Should return None when rejected
        assert result is None

        # Check stats structure
        stats = manager.get_stats()
        assert "tracker" in stats
        assert "approval" in stats


class TestTrajectoryPatternDetection:
    """Test pattern detection and similarity matching."""

    @pytest.fixture
    def tracker(self):
        """Create trajectory tracker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield TrajectoryTracker(storage_path=Path(tmpdir) / "history.json")

    def test_signature_matching(self, tracker):
        """Test exact signature matching for repeated patterns."""
        # Need 5+ tools for single occurrence to be skill-worthy
        # Or 3+ tools repeated twice
        
        # First trajectory
        tracker.start_trajectory("Debug error")
        tracker.record_tool_call("read_file", {"path": "a.py"}, "content", True)
        tracker.record_tool_call("search_files", {"regex": "error"}, "matches", True)
        tracker.record_tool_call("write_to_file", {"path": "a.py"}, None, True)
        t1_result = tracker.complete_trajectory(True, "Fixed")
        # First occurrence with 3 tools won't be skill-worthy yet
        assert t1_result is None
        
        # Get the trajectory from history for signature comparison
        t1 = tracker.trajectories[-1]

        # Second trajectory (identical pattern - now it's repeated!)
        tracker.start_trajectory("Debug error again")
        tracker.record_tool_call("read_file", {"path": "b.py"}, "content", True)
        tracker.record_tool_call("search_files", {"regex": "error"}, "matches", True)
        tracker.record_tool_call("write_to_file", {"path": "b.py"}, None, True)
        t2 = tracker.complete_trajectory(True, "Fixed")

        # Second occurrence should be skill-worthy (repeated pattern)
        assert t2 is not None
        
        # Signatures should match
        assert t1.get_signature() == t2.get_signature()

        # Should find t1 as similar to t2
        similar = tracker.get_similar_trajectories(t2, limit=5)
        assert len(similar) >= 1

    def test_jaccard_similarity(self, tracker):
        """Test Jaccard similarity for similar but not identical patterns."""
        # First trajectory (5 tools - skill-worthy)
        tracker.start_trajectory("Full workflow")
        for tool in ["read_file", "search_files", "execute_shell_command", "write_to_file", "read_file"]:
            tracker.record_tool_call(tool, {}, None, True)
        t1 = tracker.complete_trajectory(True, "Complete")
        assert t1 is not None  # 5 tools = skill-worthy

        # Second trajectory (5 tools to be skill-worthy, 3 overlap with t1)
        tracker.start_trajectory("Partial workflow")
        for tool in ["read_file", "search_files", "write_to_file", "list_files", "execute_shell_command"]:
            tracker.record_tool_call(tool, {}, None, True)
        t2 = tracker.complete_trajectory(True, "Complete")
        assert t2 is not None  # 5 tools = skill-worthy

        # Calculate expected Jaccard similarity
        # Union: {read_file, search_files, execute_shell_command, write_to_file, list_files} = 5
        # Intersection: {read_file, search_files, write_to_file, execute_shell_command} = 4
        # Similarity: 4/5 = 0.8 (above 0.7 threshold)

        similar = tracker.get_similar_trajectories(t2, limit=5)
        assert len(similar) >= 1

        found_t1 = False
        for traj in similar:
            if traj.task_description == "Full workflow":
                found_t1 = True
                # Found similar trajectory
                break

        assert found_t1, "Should find similar trajectory"

    def test_persistence(self, tracker):
        """Test trajectory history persistence."""
        # Create and complete skill-worthy trajectory (5 tools)
        tracker.start_trajectory("Persistent task")
        tracker.record_tool_call("read_file", {}, None, True)
        tracker.record_tool_call("write_to_file", {}, None, True)
        tracker.record_tool_call("execute_shell_command", {}, None, True)
        tracker.record_tool_call("search_files", {}, None, True)
        tracker.record_tool_call("read_file", {}, None, True)
        t1 = tracker.complete_trajectory(True, "Done")
        
        # Should be skill-worthy and trigger save
        assert t1 is not None

        # Create new tracker with same path
        tracker2 = TrajectoryTracker(storage_path=tracker.storage_path)

        # Pattern counts should be loaded from disk
        assert len(tracker2.pattern_counts) > 0


class TestTemplateGeneration:
    """Test skill template generation quality."""

    @pytest.fixture
    def generator(self):
        """Create template generator."""
        return SkillTemplateGenerator()

    def test_name_generation(self, generator):
        """Test auto-generated skill names."""
        trajectory = Trajectory(
            task_description="Debug Python Application Errors",
            tool_calls=[
                ToolCall("execute_shell_command", {}, None, True),
                ToolCall("read_file", {}, None, True),
                ToolCall("write_to_file", {}, None, True),
            ],
            start_time=0,
            end_time=10,
            success=True,
            outcome="Fixed errors",
        )

        skill = generator.generate_skill_from_trajectory(trajectory)

        # Name should be hyphenated, lowercase
        assert skill["name"]
        assert " " not in skill["name"]
        assert skill["name"].islower() or "-" in skill["name"]
        assert len(skill["name"]) <= 50

    def test_category_inference(self, generator):
        """Test automatic category inference."""
        # Development trajectory
        dev_trajectory = Trajectory(
            task_description="Debug Python code",
            tool_calls=[
                ToolCall("execute_shell_command", {"command": "python test.py"}, None, True),
                ToolCall("read_file", {"path": "app.py"}, None, True),
                ToolCall("write_to_file", {"path": "app.py"}, None, True),
            ],
            start_time=0,
            end_time=10,
            success=True,
            outcome="Fixed",
        )

        skill = generator.generate_skill_from_trajectory(dev_trajectory)
        assert skill["category"] == "development"

        # System trajectory (only shell/execute tools)
        system_trajectory = Trajectory(
            task_description="System monitoring",
            tool_calls=[
                ToolCall("execute_shell_command", {"command": "systemctl status"}, None, True),
                ToolCall("execute_shell_command", {"command": "journalctl -n 100"}, None, True),
                ToolCall("execute_shell_command", {"command": "df -h"}, None, True),
            ],
            start_time=0,
            end_time=10,
            success=True,
            outcome="Monitored",
        )

        skill = generator.generate_skill_from_trajectory(system_trajectory)
        assert skill["category"] == "system"

    def test_template_completeness(self, generator):
        """Test that generated templates are complete and well-formed."""
        trajectory = Trajectory(
            task_description="Deploy application",
            tool_calls=[
                ToolCall(
                    "execute_shell_command",
                    {"command": "docker build -t app ."},
                    None,
                    True,
                ),
                ToolCall(
                    "execute_shell_command",
                    {"command": "docker push app"},
                    None,
                    True,
                ),
                ToolCall(
                    "write_to_file",
                    {"path": "deployment.yaml", "content": "apiVersion: v1..."},
                    None,
                    True,
                ),
            ],
            start_time=0,
            end_time=10,
            success=True,
            outcome="Deployed",
        )

        skill = generator.generate_skill_from_trajectory(trajectory)
        content = skill["content"]

        # Check that skill was generated with proper structure
        assert "---" in content  # YAML frontmatter
        assert "name:" in content
        assert "description:" in content
        assert "required_tools:" in content
        
        # Should include the tools used
        assert "execute_shell_command" in content or "write_to_file" in content
        
        # Should have markdown content
        assert "##" in content  # Markdown headers

    def test_frontmatter_structure(self, generator):
        """Test YAML frontmatter is properly formatted."""
        trajectory = Trajectory(
            task_description="Test task",
            tool_calls=[
                ToolCall("read_file", {}, None, True),
                ToolCall("write_to_file", {}, None, True),
                ToolCall("execute_shell_command", {}, None, True),
            ],
            start_time=0,
            end_time=10,
            success=True,
            outcome="Success",
        )

        skill = generator.generate_skill_from_trajectory(trajectory, skill_name="test-skill")
        content = skill["content"]

        # Should have YAML delimiters
        assert content.startswith("---\n")
        assert "\n---\n" in content

        # Extract frontmatter
        parts = content.split("---\n")
        assert len(parts) >= 3
        frontmatter = parts[1]

        # Required fields
        assert "name: test-skill" in frontmatter
        assert "description:" in frontmatter
        assert "required_tools:" in frontmatter

        # Tools are listed (format may vary: list or array)
        assert "read_file" in frontmatter or "execute_shell_command" in frontmatter


class TestApprovalWorkflow:
    """Test approval workflow functionality."""

    @pytest.fixture
    def workflow(self):
        """Create approval workflow."""
        return SkillApprovalWorkflow(auto_approve=False)

    @pytest.mark.asyncio
    async def test_auto_approve(self):
        """Test auto-approval mode."""
        workflow = SkillApprovalWorkflow(auto_approve=True)

        trajectory = Trajectory(
            task_description="Test",
            tool_calls=[
                ToolCall("read_file", {}, None, True),
                ToolCall("write_to_file", {}, None, True),
                ToolCall("execute_shell_command", {}, None, True),
            ],
            start_time=0,
            end_time=10,
            success=True,
            outcome="Success",
        )

        result = await workflow.propose_skill(trajectory)

        # Should auto-approve
        assert result is not None
        assert result["name"]
        assert result["content"]

        # Check stats
        stats = workflow.get_stats()
        assert stats["approved"] == 1
        assert stats["approval_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_statistics(self):
        """Test approval statistics tracking."""
        workflow = SkillApprovalWorkflow(auto_approve=True)

        trajectory = Trajectory(
            task_description="Test",
            tool_calls=[
                ToolCall("read_file", {}, None, True),
                ToolCall("write_to_file", {}, None, True),
                ToolCall("execute_shell_command", {}, None, True),
            ],
            start_time=0,
            end_time=10,
            success=True,
            outcome="Success",
        )

        # Generate multiple approvals
        for _ in range(5):
            await workflow.propose_skill(trajectory)

        stats = workflow.get_stats()
        assert stats["proposed"] == 5
        assert stats["approved"] == 5
        assert stats["rejected"] == 0
        assert stats["approval_rate"] == 1.0


class TestConcurrentOperation:
    """Test thread safety and concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_tracking(self):
        """Test multiple concurrent trajectory tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = TrajectoryTracker(storage_path=Path(tmpdir) / "history.json")

            async def track_task(task_id: int):
                tracker.start_trajectory(f"Task {task_id}")
                for i in range(3):
                    tracker.record_tool_call(f"tool_{i}", {"id": task_id}, None, True)
                return tracker.complete_trajectory(True, f"Done {task_id}")

            # Run multiple tasks concurrently
            tasks = [track_task(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

            # Some may return None (not skill-worthy), but all should complete
            assert len(results) == 10
            # Results may be None for simple tasks
            
            # Trajectories should be recorded
            assert len(tracker.trajectories) >= 10

    def test_concurrent_manager_operations(self):
        """Test concurrent manager operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SkillAutoGenManager(
                storage_dir=Path(tmpdir), auto_approve=True, min_tools=3
            )

            def run_task(task_id: int):
                manager.start_task(f"Task {task_id}")
                for i in range(4):
                    manager.record_tool(f"tool_{i}", {"id": task_id}, None, True)
                return asyncio.run(
                    manager.complete_task(success=True, outcome=f"Done {task_id}")
                )

            # Sequential execution (since we're testing the manager's internal state handling)
            results = [run_task(i) for i in range(5)]

            # Check that multiple skills can be generated
            successful = [r for r in results if r is not None]
            assert len(successful) >= 1  # At least some should generate skills


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_trajectory(self):
        """Test handling of empty trajectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = TrajectoryTracker(storage_path=Path(tmpdir) / "history.json")

            tracker.start_trajectory("Empty task")
            result = tracker.complete_trajectory(True, "Nothing done")

            # Should return None for empty trajectory
            assert result is None

    def test_long_task_description(self):
        """Test handling of very long task descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SkillAutoGenManager(
                storage_dir=Path(tmpdir), auto_approve=True, min_tools=3
            )

            # Very long description
            long_desc = "A" * 1000

            manager.start_task(long_desc)
            for i in range(4):
                manager.record_tool("read_file", {"path": f"file{i}.txt"}, None, True)

            result = asyncio.run(manager.complete_task(success=True, outcome="Done"))

            if result:
                # Name should be truncated to reasonable length
                assert len(result["name"]) <= 50

    def test_special_characters_in_task(self):
        """Test handling of special characters in task descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SkillAutoGenManager(
                storage_dir=Path(tmpdir), auto_approve=True, min_tools=3
            )

            # Task with special characters
            manager.start_task("Debug C++ Code (using gdb & valgrind)")
            for i in range(4):
                manager.record_tool("execute_shell_command", {"command": "ls"}, None, True)

            result = asyncio.run(manager.complete_task(success=True, outcome="Done"))

            if result:
                # Name should be sanitized (no special chars that break filenames)
                assert "/" not in result["name"]
                assert "\\" not in result["name"]
                assert ":" not in result["name"]

    @pytest.mark.asyncio
    async def test_malformed_trajectory_data(self):
        """Test handling of malformed trajectory data."""
        generator = SkillTemplateGenerator()

        # Trajectory with None values
        trajectory = Trajectory(
            task_description="",  # Empty description
            tool_calls=[
                ToolCall("read_file", {}, None, True),
            ],
            start_time=0,
            end_time=0,
            success=True,
            outcome="",  # Empty outcome
        )

        # Should still generate valid skill
        skill = generator.generate_skill_from_trajectory(trajectory)

        assert skill is not None
        assert skill["name"]
        assert skill["content"]
        assert "---" in skill["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
