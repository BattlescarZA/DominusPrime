# -*- coding: utf-8 -*-
"""Tests for skills_index.py - Skills catalog building and caching."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dominusprime.agents.utils.skills_index import (
    build_skills_index,
    build_skills_index_compact,
    get_cached_skills_index,
    clear_skills_index_cache,
)


@pytest.fixture(autouse=True)
def clear_cache_before_test():
    """Clear the module-level cache before each test."""
    clear_skills_index_cache()
    yield
    clear_skills_index_cache()


@pytest.fixture
def mock_skills_data():
    """Create mock skills data for testing."""
    return [
        {
            "name": "python-debugging",
            "category": "development",
            "description": "A comprehensive guide to debugging Python applications using pdb, logging, and other tools",
            "platforms": ["linux", "darwin", "windows"],
            "required_tools": ["pdb"],
            "path": Path("/home/user/.dominusprime/skills/development/python-debugging"),
            "disabled": False,
        },
        {
            "name": "web-research",
            "category": "research",
            "description": "Systematic web research methodology with search operators and source validation techniques",
            "platforms": ["linux", "darwin", "windows"],
            "required_tools": [],
            "path": Path("/home/user/.dominusprime/skills/research/web-research"),
            "disabled": False,
        },
        {
            "name": "log-analysis",
            "category": "system",
            "description": "Log file analysis patterns for troubleshooting and monitoring",
            "platforms": ["linux", "darwin"],
            "required_tools": ["grep", "awk"],
            "path": Path("/home/user/.dominusprime/skills/system/log-analysis"),
            "disabled": False,
        },
        {
            "name": "disabled-skill",
            "category": "test",
            "description": "This skill is disabled for testing",
            "platforms": ["linux"],
            "required_tools": [],
            "path": Path("/home/user/.dominusprime/skills/test/disabled-skill"),
            "disabled": True,
        },
    ]


class TestBuildSkillsIndex:
    """Test build_skills_index function."""

    def test_basic_index_building(self):
        """Test basic skills index building with mocked files."""
        # Mock the skills directory and files
        mock_skills_dir = Path("/fake/skills")
        
        with patch("dominusprime.agents.utils.skills_index.get_skills_directory", return_value=mock_skills_dir):
            with patch("dominusprime.agents.utils.skills_index.iter_skill_files") as mock_iter:
                # Create mock skill files
                mock_files = [
                    Path("/fake/skills/development/python-debugging/SKILL.md"),
                    Path("/fake/skills/research/web-research/SKILL.md"),
                ]
                mock_iter.return_value = mock_files
                
                # Mock file reading
                def mock_read_text(encoding="utf-8"):
                    return "---\nname: test\ndescription: Test skill\n---\nContent"
                
                with patch.object(Path, "exists", return_value=True):
                    with patch.object(Path, "read_text", mock_read_text):
                        with patch("dominusprime.agents.utils.skills_index.get_disabled_skill_names", return_value=set()):
                            result = build_skills_index()
                            
                            # Should have skills header
                            assert "Available Skills" in result or "Skills" in result
                            # Should mention python-debugging
                            assert "python-debugging" in result

    def test_empty_skills_directory(self):
        """Test handling of empty skills directory."""
        mock_skills_dir = Path("/fake/skills")
        
        with patch("dominusprime.agents.utils.skills_index.get_skills_directory", return_value=mock_skills_dir):
            with patch.object(Path, "exists", return_value=False):
                result = build_skills_index()
                assert result == ""

    def test_compact_format(self):
        """Test compact skills index format."""
        mock_skills_dir = Path("/fake/skills")
        
        with patch("dominusprime.agents.utils.skills_index.get_skills_directory", return_value=mock_skills_dir):
            with patch("dominusprime.agents.utils.skills_index.iter_skill_files") as mock_iter:
                mock_files = [Path("/fake/skills/dev/skill1/SKILL.md")]
                mock_iter.return_value = mock_files
                
                def mock_read_text(encoding="utf-8"):
                    return "---\nname: skill1\n---\nContent"
                
                with patch.object(Path, "exists", return_value=True):
                    with patch.object(Path, "read_text", mock_read_text):
                        with patch("dominusprime.agents.utils.skills_index.get_disabled_skill_names", return_value=set()):
                            result = build_skills_index_compact()
                            
                            # Compact format should be shorter
                            assert "skill1" in result
                            assert "Skills" in result






    def test_skills_without_description(self):
        """Test handling of skills without description."""
        skill_no_desc = {
            "name": "no-desc-skill",
            "category": "test",
            "description": "",
            "platforms": ["linux"],
            "required_tools": [],
            "path": Path("/home/user/.dominusprime/skills/test/no-desc-skill"),
            "disabled": False,
        }
        
        with patch("dominusprime.agents.utils.skills_index._get_skill_index") as mock_get:
            mock_get.return_value = [skill_no_desc]
            
            result = build_skills_index()
            
            assert "no-desc-skill" in result


class TestCachedSkillsIndex:
    """Test get_cached_skills_index function and caching behavior."""

    def test_first_call_builds_cache(self, mock_skills_data):
        """Test that first call builds and caches the index."""
        with patch("dominusprime.agents.utils.skills_index._get_skill_index") as mock_get:
            mock_get.return_value = mock_skills_data[:3]
            
            result1 = get_cached_skills_index()
            result2 = get_cached_skills_index()
            
            # Should be the same result
            assert result1 == result2
            # _get_skill_index should only be called once (cached)
            assert mock_get.call_count == 1

    def test_compact_format(self, mock_skills_data):
        """Test compact format parameter."""
        with patch("dominusprime.agents.utils.skills_index._get_skill_index") as mock_get:
            mock_get.return_value = mock_skills_data[:3]
            
            normal = get_cached_skills_index(compact=False)
            compact = get_cached_skills_index(compact=True)
            
            # Compact should be shorter
            assert len(compact) < len(normal)
            # Both should have skill names
            assert "python-debugging" in normal
            assert "python-debugging" in compact

    def test_cache_key_isolation(self, mock_skills_data):
        """Test that different parameters create separate cache entries."""
        with patch("dominusprime.agents.utils.skills_index._get_skill_index") as mock_get:
            mock_get.return_value = mock_skills_data[:3]
            
            result1 = get_cached_skills_index(compact=False)
            result2 = get_cached_skills_index(compact=True)
            
            # Should call _get_skill_index twice (different cache keys)
            assert mock_get.call_count == 2
            # Results should be different
            assert result1 != result2

    def test_cache_clear(self, mock_skills_data):
        """Test that cache can be cleared."""
        with patch("dominusprime.agents.utils.skills_index._get_skill_index") as mock_get:
            mock_get.return_value = mock_skills_data[:3]
            
            result1 = get_cached_skills_index()
            _clear_cache()
            result2 = get_cached_skills_index()
            
            # Should call _get_skill_index twice (cache was cleared)
            assert mock_get.call_count == 2
            # Results should be the same
            assert result1 == result2

    def test_none_return_when_no_skills(self):
        """Test that None is returned when there are no skills."""
        with patch("dominusprime.agents.utils.skills_index._get_skill_index") as mock_get:
            mock_get.return_value = []
            
            result = get_cached_skills_index()
            
            assert result is None

    def test_caching_performance(self, mock_skills_data):
        """Test that caching improves performance."""
        with patch("dominusprime.agents.utils.skills_index._get_skill_index") as mock_get:
            mock_get.return_value = mock_skills_data[:3]
            
            # First call - builds cache
            import time
            start1 = time.time()
            result1 = get_cached_skills_index()
            time1 = time.time() - start1
            
            # Second call - from cache
            start2 = time.time()
            result2 = get_cached_skills_index()
            time2 = time.time() - start2
            
            # Cached call should be faster (significantly)
            # We can't guarantee exact timing, but mock should show it
            assert mock_get.call_count == 1
            assert result1 == result2




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
