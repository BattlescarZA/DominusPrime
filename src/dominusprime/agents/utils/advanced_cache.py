# -*- coding: utf-8 -*-
"""
Advanced Caching - LRU cache with disk persistence.

Features:
- LRU (Least Recently Used) eviction policy
- Configurable size limits
- Disk persistence with JSON serialization
- TTL (time-to-live) support
- Thread-safe operations
"""

import json
import logging
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU cache with disk persistence.
    
    Features:
    - LRU eviction when max_size exceeded
    - Optional TTL (time-to-live) per entry
    - Disk persistence to JSON file
    - Automatic loading/saving
    """
    
    def __init__(
        self,
        max_size: int = 100,
        ttl: Optional[float] = None,
        disk_path: Optional[Path] = None,
        auto_persist: bool = True,
    ):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries (default: 100)
            ttl: Time-to-live in seconds (None = no expiration)
            disk_path: Path to persist cache to disk
            auto_persist: Automatically save to disk on updates
        """
        self.max_size = max_size
        self.ttl = ttl
        self.disk_path = disk_path
        self.auto_persist = auto_persist
        
        # OrderedDict maintains insertion order for LRU
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        
        # Load from disk if path exists
        if self.disk_path and self.disk_path.exists():
            self._load_from_disk()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key not in self._cache:
                return default
            
            entry = self._cache[key]
            
            # Check TTL expiration
            if self._is_expired(entry):
                del self._cache[key]
                if self.auto_persist:
                    self._save_to_disk()
                return default
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override for this entry (seconds)
        """
        with self._lock:
            # Create entry with metadata
            entry = {
                "value": value,
                "created_at": time.time(),
                "ttl": ttl if ttl is not None else self.ttl,
            }
            
            # Update or insert
            if key in self._cache:
                del self._cache[key]
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            # Evict oldest if over max_size
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)  # Remove oldest (first item)
            
            # Persist to disk
            if self.auto_persist:
                self._save_to_disk()
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if self.auto_persist:
                    self._save_to_disk()
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            if self.auto_persist:
                self._save_to_disk()
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[float] = None,
    ) -> Any:
        """
        Get value from cache, or compute and cache it if missing.
        
        Args:
            key: Cache key
            factory: Function to compute value if not in cache
            ttl: Optional TTL for this entry
            
        Returns:
            Cached or newly computed value
        """
        # Try to get existing value
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute new value
        value = factory()
        self.set(key, value, ttl=ttl)
        return value
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys and self.auto_persist:
                self._save_to_disk()
            
            return len(expired_keys)
    
    def size(self) -> int:
        """Get current number of cached entries."""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list[str]:
        """Get list of all cache keys."""
        with self._lock:
            return list(self._cache.keys())
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats (size, max_size, etc.)
        """
        with self._lock:
            expired_count = sum(
                1 for entry in self._cache.values()
                if self._is_expired(entry)
            )
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "expired_count": expired_count,
                "ttl": self.ttl,
                "disk_path": str(self.disk_path) if self.disk_path else None,
                "auto_persist": self.auto_persist,
            }
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry has expired."""
        if entry.get("ttl") is None:
            return False
        
        age = time.time() - entry["created_at"]
        return age > entry["ttl"]
    
    def _save_to_disk(self) -> None:
        """Save cache to disk as JSON."""
        if not self.disk_path:
            return
        
        try:
            # Ensure parent directory exists
            self.disk_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert cache to serializable format
            data = {
                "max_size": self.max_size,
                "ttl": self.ttl,
                "entries": dict(self._cache),
            }
            
            # Write atomically
            temp_path = self.disk_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Atomic replace
            temp_path.replace(self.disk_path)
            
            logger.debug(f"Saved cache to {self.disk_path} ({len(self._cache)} entries)")
        
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}", exc_info=True)
    
    def _load_from_disk(self) -> None:
        """Load cache from disk JSON."""
        if not self.disk_path or not self.disk_path.exists():
            return
        
        try:
            with open(self.disk_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore entries
            entries = data.get("entries", {})
            for key, entry in entries.items():
                # Skip expired entries
                if not self._is_expired(entry):
                    self._cache[key] = entry
            
            logger.info(f"Loaded cache from {self.disk_path} ({len(self._cache)} entries)")
        
        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}", exc_info=True)
    
    def persist(self) -> None:
        """Manually persist cache to disk."""
        with self._lock:
            self._save_to_disk()
    
    def __len__(self) -> int:
        """Get number of cached entries."""
        return self.size()
    
    def __contains__(self, key: str) -> bool:
        """Check if key is in cache (non-expired)."""
        return self.get(key) is not None
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LRUCache(size={len(self._cache)}, max_size={self.max_size}, "
            f"ttl={self.ttl}, disk_path={self.disk_path})"
        )


# Global cache instances for common use cases
_skills_cache: Optional[LRUCache] = None
_context_cache: Optional[LRUCache] = None


def get_skills_cache(cache_dir: Optional[Path] = None) -> LRUCache:
    """
    Get global skills cache instance.
    
    Args:
        cache_dir: Directory for cache persistence
        
    Returns:
        LRUCache instance for skills
    """
    global _skills_cache
    
    if _skills_cache is None:
        disk_path = None
        if cache_dir:
            disk_path = cache_dir / "skills_cache.json"
        
        _skills_cache = LRUCache(
            max_size=50,  # Cache up to 50 skills
            ttl=3600,  # 1 hour TTL
            disk_path=disk_path,
            auto_persist=True,
        )
    
    return _skills_cache


def get_context_cache(cache_dir: Optional[Path] = None) -> LRUCache:
    """
    Get global context cache instance.
    
    Args:
        cache_dir: Directory for cache persistence
        
    Returns:
        LRUCache instance for context data
    """
    global _context_cache
    
    if _context_cache is None:
        disk_path = None
        if cache_dir:
            disk_path = cache_dir / "context_cache.json"
        
        _context_cache = LRUCache(
            max_size=100,  # Cache up to 100 context entries
            ttl=1800,  # 30 minutes TTL
            disk_path=disk_path,
            auto_persist=True,
        )
    
    return _context_cache


__all__ = [
    "LRUCache",
    "get_skills_cache",
    "get_context_cache",
]
