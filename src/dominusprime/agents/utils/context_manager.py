# -*- coding: utf-8 -*-
"""
Context Manager - Automatic context length detection and compression.

Features:
- Auto-detect context length from model provider metadata
- Default to 128k tokens when detection fails
- Automatic compression at 90% threshold
- User-configurable context limits
- Provider-specific optimizations
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Default context length (128k tokens)
DEFAULT_CONTEXT_LENGTH = 128 * 1024  # 128k tokens

# Compression trigger threshold (90%)
COMPRESSION_THRESHOLD = 0.90

# Known model context lengths (fallback when API doesn't provide)
KNOWN_MODEL_CONTEXTS = {
    # OpenAI models
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-4-1106-preview": 128000,
    "gpt-4-0125-preview": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-3.5-turbo-1106": 16385,
    "gpt-3.5-turbo-0125": 16385,
    
    # Anthropic models
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-3-5-sonnet": 200000,
    "claude-2.1": 200000,
    "claude-2": 100000,
    "claude-instant": 100000,
    
    # Google models
    "gemini-pro": 32768,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    
    # Other providers
    "llama-2-70b": 4096,
    "llama-3-70b": 8192,
    "mistral-large": 32768,
    "mixtral-8x7b": 32768,
}


@dataclass
class ContextConfig:
    """Context configuration for a model."""
    max_tokens: int
    compression_threshold: float = COMPRESSION_THRESHOLD
    provider: Optional[str] = None
    model_name: Optional[str] = None
    user_override: bool = False


class ContextManager:
    """Manages context length detection, tracking, and compression."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        max_tokens: Optional[int] = None,
        config_path: Optional[Path] = None,
    ):
        """
        Initialize context manager.
        
        Args:
            model_name: Name of the model (e.g., "gpt-4-turbo")
            provider: Provider name (e.g., "openai", "anthropic")
            max_tokens: Manual override for max context tokens
            config_path: Path to user config file for overrides
        """
        self.model_name = model_name
        self.provider = provider
        self.config_path = config_path
        
        # Load user overrides if config exists
        self.user_overrides = self._load_user_overrides()
        
        # Detect or set context length
        self.config = self._detect_context_config(
            model_name=model_name,
            provider=provider,
            max_tokens=max_tokens,
        )
        
        logger.info(
            f"Context manager initialized: {self.config.max_tokens} tokens "
            f"(provider={self.config.provider}, model={self.config.model_name}, "
            f"user_override={self.config.user_override})"
        )
    
    def _load_user_overrides(self) -> Dict[str, int]:
        """Load user-defined context length overrides from config."""
        if not self.config_path or not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("context_overrides", {})
        except Exception as e:
            logger.warning(f"Failed to load context overrides: {e}")
            return {}
    
    def _detect_context_config(
        self,
        model_name: Optional[str],
        provider: Optional[str],
        max_tokens: Optional[int],
    ) -> ContextConfig:
        """
        Detect context configuration from multiple sources.
        
        Priority:
        1. Explicit max_tokens parameter
        2. User config overrides
        3. Model provider API metadata
        4. Known model context table
        5. Default (128k)
        """
        # 1. Explicit override
        if max_tokens is not None:
            logger.info(f"Using explicit context length: {max_tokens} tokens")
            return ContextConfig(
                max_tokens=max_tokens,
                provider=provider,
                model_name=model_name,
                user_override=True,
            )
        
        # 2. User config overrides
        if model_name and model_name in self.user_overrides:
            tokens = self.user_overrides[model_name]
            logger.info(f"Using user override for {model_name}: {tokens} tokens")
            return ContextConfig(
                max_tokens=tokens,
                provider=provider,
                model_name=model_name,
                user_override=True,
            )
        
        # 3. Try to detect from provider API
        detected_tokens = self._detect_from_provider(provider, model_name)
        if detected_tokens:
            logger.info(f"Detected from provider API: {detected_tokens} tokens")
            return ContextConfig(
                max_tokens=detected_tokens,
                provider=provider,
                model_name=model_name,
                user_override=False,
            )
        
        # 4. Known model context table
        if model_name:
            # Try exact match first
            if model_name in KNOWN_MODEL_CONTEXTS:
                tokens = KNOWN_MODEL_CONTEXTS[model_name]
                logger.info(f"Using known context for {model_name}: {tokens} tokens")
                return ContextConfig(
                    max_tokens=tokens,
                    provider=provider,
                    model_name=model_name,
                    user_override=False,
                )
            
            # Try partial match (e.g., "gpt-4-turbo-2024" matches "gpt-4-turbo")
            # Sort by length descending to match longest prefix first
            sorted_models = sorted(KNOWN_MODEL_CONTEXTS.items(), key=lambda x: len(x[0]), reverse=True)
            for known_model, tokens in sorted_models:
                if model_name.startswith(known_model):
                    logger.info(
                        f"Using known context for {known_model} "
                        f"(matched {model_name}): {tokens} tokens"
                    )
                    return ContextConfig(
                        max_tokens=tokens,
                        provider=provider,
                        model_name=model_name,
                        user_override=False,
                    )
        
        # 5. Default to 128k
        logger.warning(
            f"Could not detect context length for {model_name} ({provider}), "
            f"defaulting to {DEFAULT_CONTEXT_LENGTH} tokens"
        )
        return ContextConfig(
            max_tokens=DEFAULT_CONTEXT_LENGTH,
            provider=provider,
            model_name=model_name,
            user_override=False,
        )
    
    def _detect_from_provider(
        self,
        provider: Optional[str],
        model_name: Optional[str],
    ) -> Optional[int]:
        """
        Attempt to detect context length from provider API metadata.
        
        This tries to query the provider's API for model information.
        Returns None if detection fails.
        """
        if not provider or not model_name:
            return None
        
        try:
            if provider.lower() in ["openai", "azure-openai"]:
                return self._detect_openai_context(model_name)
            elif provider.lower() == "anthropic":
                return self._detect_anthropic_context(model_name)
            elif provider.lower() == "google":
                return self._detect_google_context(model_name)
        except Exception as e:
            logger.debug(f"Failed to detect context from {provider} API: {e}")
        
        return None
    
    def _detect_openai_context(self, model_name: str) -> Optional[int]:
        """Detect context length from OpenAI API."""
        try:
            import openai
            
            # Try to get model info from OpenAI API
            # Note: This requires openai library to be installed
            client = openai.OpenAI()
            models = client.models.list()
            
            for model in models.data:
                if model.id == model_name:
                    # Some models have context_length in metadata
                    if hasattr(model, 'context_length'):
                        return model.context_length
                    break
        except Exception as e:
            logger.debug(f"OpenAI context detection failed: {e}")
        
        return None
    
    def _detect_anthropic_context(self, model_name: str) -> Optional[int]:
        """Detect context length from Anthropic API."""
        # Anthropic doesn't expose model metadata via API
        # Fall back to known contexts
        return None
    
    def _detect_google_context(self, model_name: str) -> Optional[int]:
        """Detect context length from Google API."""
        try:
            import google.generativeai as genai
            
            # Google's API provides model info
            model = genai.get_model(f"models/{model_name}")
            if hasattr(model, 'input_token_limit'):
                return model.input_token_limit
        except Exception as e:
            logger.debug(f"Google context detection failed: {e}")
        
        return None
    
    def should_compress(self, current_tokens: int) -> bool:
        """
        Check if context should be compressed.
        
        Args:
            current_tokens: Current number of tokens in context
            
        Returns:
            True if compression threshold reached
        """
        usage_ratio = current_tokens / self.config.max_tokens
        should_compress = usage_ratio >= self.config.compression_threshold
        
        if should_compress:
            logger.info(
                f"Compression threshold reached: {current_tokens}/{self.config.max_tokens} "
                f"({usage_ratio:.1%} >= {self.config.compression_threshold:.1%})"
            )
        
        return should_compress
    
    def get_compression_target(self) -> int:
        """
        Get target token count after compression.
        
        Returns half of max tokens to leave headroom.
        """
        return self.config.max_tokens // 2
    
    def get_max_tokens(self) -> int:
        """Get maximum context length in tokens."""
        return self.config.max_tokens
    
    def get_remaining_tokens(self, current_tokens: int) -> int:
        """Get remaining tokens before hitting limit."""
        return max(0, self.config.max_tokens - current_tokens)
    
    def get_usage_ratio(self, current_tokens: int) -> float:
        """Get current context usage ratio (0.0 to 1.0)."""
        return max(0.0, min(1.0, current_tokens / self.config.max_tokens))
    
    def update_max_tokens(self, new_max: int) -> None:
        """
        Update maximum context length (user override).
        
        Args:
            new_max: New maximum token count
        """
        logger.info(f"Updating context length: {self.config.max_tokens} -> {new_max}")
        self.config.max_tokens = new_max
        self.config.user_override = True
        
        # Save to user config if path is set
        if self.config_path and self.model_name:
            self._save_user_override(self.model_name, new_max)
    
    def _save_user_override(self, model_name: str, max_tokens: int) -> None:
        """Save user override to config file."""
        try:
            config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if "context_overrides" not in config:
                config["context_overrides"] = {}
            
            config["context_overrides"][model_name] = max_tokens
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved context override for {model_name}: {max_tokens}")
        except Exception as e:
            logger.error(f"Failed to save context override: {e}")
    
    def get_status(self, current_tokens: int) -> Dict[str, Any]:
        """
        Get current context status.
        
        Args:
            current_tokens: Current token count
            
        Returns:
            Status dictionary with metrics
        """
        return {
            "current_tokens": current_tokens,
            "max_tokens": self.config.max_tokens,
            "remaining_tokens": self.get_remaining_tokens(current_tokens),
            "usage_ratio": self.get_usage_ratio(current_tokens),
            "should_compress": self.should_compress(current_tokens),
            "compression_threshold": self.config.compression_threshold,
            "compression_target": self.get_compression_target(),
            "provider": self.config.provider,
            "model_name": self.config.model_name,
            "user_override": self.config.user_override,
        }


def create_context_manager(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    max_tokens: Optional[int] = None,
    config_path: Optional[Path] = None,
) -> ContextManager:
    """
    Factory function to create a context manager.
    
    Args:
        model_name: Model name for context detection
        provider: Provider name (openai, anthropic, google, etc.)
        max_tokens: Manual context length override
        config_path: Path to user configuration file
        
    Returns:
        Configured ContextManager instance
        
    Example:
        >>> cm = create_context_manager(model_name="gpt-4-turbo", provider="openai")
        >>> cm.get_max_tokens()
        128000
        >>> cm.should_compress(115200)  # 90% of 128k
        True
    """
    return ContextManager(
        model_name=model_name,
        provider=provider,
        max_tokens=max_tokens,
        config_path=config_path,
    )
