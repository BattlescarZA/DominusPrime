# -*- coding: utf-8 -*-
"""Tests for context_manager.py - Context length detection and compression."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dominusprime.agents.utils.context_manager import (
    ContextManager,
    ContextConfig,
    create_context_manager,
    DEFAULT_CONTEXT_LENGTH,
    COMPRESSION_THRESHOLD,
    KNOWN_MODEL_CONTEXTS,
)


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "context_config.json"
    return config_file


class TestContextConfig:
    """Test ContextConfig dataclass."""
    
    def test_basic_config(self):
        """Test basic config creation."""
        config = ContextConfig(
            max_tokens=128000,
            provider="openai",
            model_name="gpt-4-turbo",
        )
        
        assert config.max_tokens == 128000
        assert config.provider == "openai"
        assert config.model_name == "gpt-4-turbo"
        assert config.compression_threshold == COMPRESSION_THRESHOLD
        assert config.user_override is False
    
    def test_config_with_custom_threshold(self):
        """Test config with custom compression threshold."""
        config = ContextConfig(
            max_tokens=100000,
            compression_threshold=0.85,
            user_override=True,
        )
        
        assert config.compression_threshold == 0.85
        assert config.user_override is True


class TestContextManagerInit:
    """Test ContextManager initialization."""
    
    def test_init_with_known_model(self):
        """Test initialization with a known model."""
        cm = ContextManager(model_name="gpt-4-turbo", provider="openai")
        
        assert cm.config.max_tokens == 128000
        assert cm.config.model_name == "gpt-4-turbo"
        assert cm.config.provider == "openai"
        assert cm.config.user_override is False
    
    def test_init_with_manual_override(self):
        """Test initialization with manual max_tokens override."""
        cm = ContextManager(
            model_name="gpt-4",
            provider="openai",
            max_tokens=50000,
        )
        
        assert cm.config.max_tokens == 50000
        assert cm.config.user_override is True
    
    def test_init_with_unknown_model_defaults_to_128k(self):
        """Test that unknown models default to 128k."""
        cm = ContextManager(
            model_name="unknown-model-xyz",
            provider="unknown-provider",
        )
        
        assert cm.config.max_tokens == DEFAULT_CONTEXT_LENGTH
        assert cm.config.max_tokens == 128 * 1024
    
    def test_init_with_user_config_override(self, temp_config_file):
        """Test initialization with user config file override."""
        # Create config with override
        config_data = {
            "context_overrides": {
                "gpt-4": 64000
            }
        }
        with open(temp_config_file, 'w') as f:
            json.dump(config_data, f)
        
        cm = ContextManager(
            model_name="gpt-4",
            provider="openai",
            config_path=temp_config_file,
        )
        
        assert cm.config.max_tokens == 64000
        assert cm.config.user_override is True


class TestKnownModelDetection:
    """Test detection from KNOWN_MODEL_CONTEXTS table."""
    
    def test_exact_model_match(self):
        """Test exact model name match."""
        cm = ContextManager(model_name="gpt-4-turbo")
        assert cm.config.max_tokens == 128000
        
        cm = ContextManager(model_name="claude-3-opus")
        assert cm.config.max_tokens == 200000
        
        cm = ContextManager(model_name="gemini-1.5-pro")
        assert cm.config.max_tokens == 1000000
    
    def test_partial_model_match(self):
        """Test partial model name matching."""
        # "gpt-4-turbo-2024" should match "gpt-4-turbo"
        cm = ContextManager(model_name="gpt-4-turbo-2024-01-25")
        assert cm.config.max_tokens == 128000
        
        # "claude-3-opus-latest" should match "claude-3-opus"
        cm = ContextManager(model_name="claude-3-opus-20240229")
        assert cm.config.max_tokens == 200000
    
    def test_all_known_models(self):
        """Test that all known models are correctly detected."""
        for model_name, expected_tokens in KNOWN_MODEL_CONTEXTS.items():
            cm = ContextManager(model_name=model_name)
            assert cm.config.max_tokens == expected_tokens


class TestCompressionLogic:
    """Test compression threshold and triggering logic."""
    
    def test_should_compress_below_threshold(self):
        """Test that compression is not triggered below threshold."""
        cm = ContextManager(max_tokens=100000)
        
        # 89% usage - should not compress
        assert cm.should_compress(89000) is False
        
        # 50% usage - should not compress
        assert cm.should_compress(50000) is False
    
    def test_should_compress_at_threshold(self):
        """Test that compression is triggered at 90% threshold."""
        cm = ContextManager(max_tokens=100000)
        
        # Exactly 90% - should compress
        assert cm.should_compress(90000) is True
        
        # 91% - should compress
        assert cm.should_compress(91000) is True
        
        # 95% - should compress
        assert cm.should_compress(95000) is True
    
    def test_custom_compression_threshold(self):
        """Test custom compression threshold."""
        cm = ContextManager(max_tokens=100000)
        cm.config.compression_threshold = 0.85  # 85% threshold
        
        # 84% - should not compress
        assert cm.should_compress(84000) is False
        
        # 85% - should compress
        assert cm.should_compress(85000) is True
    
    def test_compression_target(self):
        """Test compression target calculation."""
        cm = ContextManager(max_tokens=100000)
        
        # Target should be half of max
        assert cm.get_compression_target() == 50000
        
        cm = ContextManager(max_tokens=128000)
        assert cm.get_compression_target() == 64000


class TestTokenTracking:
    """Test token tracking and status methods."""
    
    def test_get_max_tokens(self):
        """Test getting maximum token count."""
        cm = ContextManager(max_tokens=128000)
        assert cm.get_max_tokens() == 128000
    
    def test_get_remaining_tokens(self):
        """Test calculating remaining tokens."""
        cm = ContextManager(max_tokens=100000)
        
        assert cm.get_remaining_tokens(30000) == 70000
        assert cm.get_remaining_tokens(90000) == 10000
        assert cm.get_remaining_tokens(100000) == 0
        
        # Over limit should return 0
        assert cm.get_remaining_tokens(110000) == 0
    
    def test_get_usage_ratio(self):
        """Test calculating usage ratio."""
        cm = ContextManager(max_tokens=100000)
        
        assert cm.get_usage_ratio(50000) == 0.5
        assert cm.get_usage_ratio(90000) == 0.9
        assert cm.get_usage_ratio(100000) == 1.0
        
        # Over limit should cap at 1.0
        assert cm.get_usage_ratio(110000) == 1.0
    
    def test_get_status(self):
        """Test getting complete status."""
        cm = ContextManager(
            model_name="gpt-4-turbo",
            provider="openai",
            max_tokens=128000,
        )
        
        status = cm.get_status(current_tokens=115200)  # 90%
        
        assert status["current_tokens"] == 115200
        assert status["max_tokens"] == 128000
        assert status["remaining_tokens"] == 12800
        assert status["usage_ratio"] == 0.9
        assert status["should_compress"] is True
        assert status["compression_threshold"] == 0.9
        assert status["compression_target"] == 64000
        assert status["provider"] == "openai"
        assert status["model_name"] == "gpt-4-turbo"
        assert status["user_override"] is True


class TestUserOverrides:
    """Test user configuration overrides."""
    
    def test_update_max_tokens(self, temp_config_file):
        """Test updating max tokens at runtime."""
        cm = ContextManager(
            model_name="gpt-4",
            max_tokens=128000,
            config_path=temp_config_file,
        )
        
        assert cm.config.max_tokens == 128000
        
        # Update to new value
        cm.update_max_tokens(200000)
        
        assert cm.config.max_tokens == 200000
        assert cm.config.user_override is True
    
    def test_save_user_override(self, temp_config_file):
        """Test saving user override to config file."""
        cm = ContextManager(
            model_name="gpt-4",
            config_path=temp_config_file,
        )
        
        # Update and save
        cm.update_max_tokens(150000)
        
        # Verify file was created and contains override
        assert temp_config_file.exists()
        
        with open(temp_config_file, 'r') as f:
            config = json.load(f)
        
        assert "context_overrides" in config
        assert config["context_overrides"]["gpt-4"] == 150000
    
    def test_load_existing_overrides(self, temp_config_file):
        """Test loading existing overrides from file."""
        # Create config with multiple overrides
        config_data = {
            "context_overrides": {
                "gpt-4": 64000,
                "claude-3-opus": 150000,
            }
        }
        with open(temp_config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Test GPT-4 override
        cm1 = ContextManager(
            model_name="gpt-4",
            config_path=temp_config_file,
        )
        assert cm1.config.max_tokens == 64000
        
        # Test Claude override
        cm2 = ContextManager(
            model_name="claude-3-opus",
            config_path=temp_config_file,
        )
        assert cm2.config.max_tokens == 150000


class TestProviderDetection:
    """Test provider API detection (mocked)."""
    
    def test_openai_detection_fallback(self):
        """Test OpenAI detection with fallback."""
        with patch("dominusprime.agents.utils.context_manager.ContextManager._detect_openai_context", return_value=None):
            cm = ContextManager(model_name="gpt-4-turbo", provider="openai")
            # Should fall back to known contexts
            assert cm.config.max_tokens == 128000
    
    def test_anthropic_detection_fallback(self):
        """Test Anthropic detection with fallback."""
        with patch("dominusprime.agents.utils.context_manager.ContextManager._detect_anthropic_context", return_value=None):
            cm = ContextManager(model_name="claude-3-opus", provider="anthropic")
            # Should fall back to known contexts
            assert cm.config.max_tokens == 200000
    
    def test_google_detection_fallback(self):
        """Test Google detection with fallback."""
        with patch("dominusprime.agents.utils.context_manager.ContextManager._detect_google_context", return_value=None):
            cm = ContextManager(model_name="gemini-1.5-pro", provider="google")
            # Should fall back to known contexts
            assert cm.config.max_tokens == 1000000


class TestFactoryFunction:
    """Test create_context_manager factory function."""
    
    def test_factory_basic(self):
        """Test factory function with basic parameters."""
        cm = create_context_manager(
            model_name="gpt-4-turbo",
            provider="openai",
        )
        
        assert isinstance(cm, ContextManager)
        assert cm.config.max_tokens == 128000
    
    def test_factory_with_override(self):
        """Test factory function with manual override."""
        cm = create_context_manager(
            model_name="gpt-4",
            provider="openai",
            max_tokens=75000,
        )
        
        assert cm.config.max_tokens == 75000
        assert cm.config.user_override is True
    
    def test_factory_with_config_path(self, temp_config_file):
        """Test factory function with config file."""
        config_data = {"context_overrides": {"test-model": 99000}}
        with open(temp_config_file, 'w') as f:
            json.dump(config_data, f)
        
        cm = create_context_manager(
            model_name="test-model",
            config_path=temp_config_file,
        )
        
        assert cm.config.max_tokens == 99000


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_no_model_name_defaults_to_128k(self):
        """Test initialization with no model name."""
        cm = ContextManager()
        assert cm.config.max_tokens == DEFAULT_CONTEXT_LENGTH
    
    def test_empty_model_name(self):
        """Test initialization with empty model name."""
        cm = ContextManager(model_name="")
        assert cm.config.max_tokens == DEFAULT_CONTEXT_LENGTH
    
    def test_invalid_config_file(self, tmp_path):
        """Test handling of invalid config file."""
        bad_config = tmp_path / "bad_config.json"
        with open(bad_config, 'w') as f:
            f.write("not valid json{{{")
        
        # Should not crash, just use defaults
        cm = ContextManager(
            model_name="gpt-4",
            config_path=bad_config,
        )
        assert cm.config.max_tokens == 8192  # Known gpt-4 default
    
    def test_zero_tokens(self):
        """Test getting remaining tokens when current is zero."""
        cm = ContextManager(max_tokens=100000)
        assert cm.get_remaining_tokens(0) == 100000
        assert cm.get_usage_ratio(0) == 0.0
        assert cm.should_compress(0) is False
    
    def test_negative_current_tokens(self):
        """Test handling of negative token counts."""
        cm = ContextManager(max_tokens=100000)
        # Should handle gracefully
        assert cm.get_usage_ratio(-100) >= 0.0


class TestIntegration:
    """Integration tests for context manager."""
    
    def test_full_workflow(self, temp_config_file):
        """Test complete workflow from creation to compression."""
        # 1. Create manager for GPT-4 Turbo
        cm = create_context_manager(
            model_name="gpt-4-turbo",
            provider="openai",
            config_path=temp_config_file,
        )
        
        assert cm.get_max_tokens() == 128000
        
        # 2. Check status at 50% usage
        status = cm.get_status(64000)
        assert status["should_compress"] is False
        assert status["usage_ratio"] == 0.5
        
        # 3. Check status at 90% usage (trigger compression)
        status = cm.get_status(115200)
        assert status["should_compress"] is True
        assert status["compression_target"] == 64000
        
        # 4. Update max tokens
        cm.update_max_tokens(200000)
        assert cm.get_max_tokens() == 200000
        
        # 5. Verify override was saved
        assert temp_config_file.exists()
        with open(temp_config_file, 'r') as f:
            config = json.load(f)
        assert config["context_overrides"]["gpt-4-turbo"] == 200000
        
        # 6. Create new manager - should load override
        cm2 = create_context_manager(
            model_name="gpt-4-turbo",
            provider="openai",
            config_path=temp_config_file,
        )
        assert cm2.get_max_tokens() == 200000
    
    def test_multiple_models(self, temp_config_file):
        """Test managing multiple models."""
        models = [
            ("gpt-4-turbo", "openai", 128000),
            ("claude-3-opus", "anthropic", 200000),
            ("gemini-1.5-pro", "google", 1000000),
        ]
        
        for model_name, provider, expected_tokens in models:
            cm = create_context_manager(
                model_name=model_name,
                provider=provider,
                config_path=temp_config_file,
            )
            assert cm.get_max_tokens() == expected_tokens
            
            # Test compression threshold
            threshold_tokens = int(expected_tokens * 0.9)
            assert cm.should_compress(threshold_tokens) is True
            assert cm.should_compress(threshold_tokens - 1) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
