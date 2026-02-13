# services/cache_service.py - In-memory caching with TTL
import time
import hashlib
from typing import Any, Dict, Optional
from functools import wraps
from config import CACHE_ENABLED, CACHE_TTL, TRANSCRIPT_CACHE_TTL, RESPONSE_CACHE_MAX_SIZE


class TTLCache:
    """Simple in-memory cache with TTL (time-to-live) support."""
    
    def __init__(self, max_size: int = 256, default_ttl: int = 3600):
        self._cache: Dict[str, tuple] = {}  # {key: (value, expiry_time)}
        self._max_size = max_size
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if not CACHE_ENABLED:
            return None
            
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                # Expired, remove it
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        if not CACHE_ENABLED:
            return
            
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        expiry = time.time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def _evict_oldest(self) -> None:
        """Remove the oldest entry based on expiry time."""
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
    
    def stats(self) -> dict:
        """Get cache statistics."""
        valid_count = sum(1 for _, (_, exp) in self._cache.items() if time.time() < exp)
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_count,
            "max_size": self._max_size
        }


# Global cache instances
transcript_cache = TTLCache(max_size=50, default_ttl=TRANSCRIPT_CACHE_TTL)
response_cache = TTLCache(max_size=RESPONSE_CACHE_MAX_SIZE, default_ttl=CACHE_TTL)


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()


def cached_response(ttl: Optional[int] = None):
    """Decorator to cache function responses."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Check cache first
            cached = response_cache.get(key)
            if cached is not None:
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            response_cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


def get_cached_transcript(video_id: str) -> Optional[str]:
    """Get transcript from cache."""
    return transcript_cache.get(f"transcript:{video_id}")


def cache_transcript(video_id: str, transcript: str) -> None:
    """Cache a transcript."""
    transcript_cache.set(f"transcript:{video_id}", transcript)


def get_cache_stats() -> dict:
    """Get statistics for all caches."""
    return {
        "transcript_cache": transcript_cache.stats(),
        "response_cache": response_cache.stats()
    }
