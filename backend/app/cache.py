"""Caching implementation for the Slack Trophy backend."""
import time
from typing import Any, Optional
from threading import Lock


class CacheEntry:
    """Cache entry with timestamp and data."""
    
    def __init__(self, data: Any, ttl: int):
        """Initialize cache entry.
        
        Args:
            data: Data to cache
            ttl: Time to live in seconds
        """
        self.data = data
        self.timestamp = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired.
        
        Returns:
            True if expired, False otherwise
        """
        return (time.time() - self.timestamp) > self.ttl


class Cache:
    """Thread-safe in-memory cache with TTL."""
    
    def __init__(self, default_ttl: int = 600):
        """Initialize cache.
        
        Args:
            default_ttl: Default time to live in seconds (default: 10 minutes)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        with self._lock:
            cache_ttl = ttl if ttl is not None else self.default_ttl
            self._cache[key] = CacheEntry(value, cache_ttl)
    
    def delete(self, key: str) -> None:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
        """
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def generate_key(self, channel_id: str, start_date: str, end_date: str, 
                     unique_flag: bool, item_type: str) -> str:
        """Generate cache key for photos/messages.
        
        Args:
            channel_id: Slack channel ID
            start_date: Start date string
            end_date: End date string
            unique_flag: Whether unique reactions are enabled
            item_type: Type of items ("photos" or "messages")
        
        Returns:
            Cache key string
        """
        unique_str = "unique" if unique_flag else "all"
        return f"{channel_id}:{start_date}:{end_date}:{unique_str}:{item_type}"


# Global cache instance
cache = Cache()

