"""
In-Memory Cache Service
Redis olmadan basit in-memory cache mekanizması
"""

from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import threading

class CacheEntry:
    """Cache entry sınıfı"""
    def __init__(self, data: Any, ttl: int = 300):
        self.data = data
        self.created_at = datetime.now()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Cache entry'nin süresi dolmuş mu?"""
        return (datetime.now() - self.created_at).total_seconds() > self.ttl
    
    def is_valid(self) -> bool:
        """Cache entry geçerli mi?"""
        return not self.is_expired()


class CacheService:
    """In-memory cache servisi (Redis alternatifi)"""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        # Default TTL: 5 dakika (300 saniye)
        self.default_ttl = 300
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den değer alır"""
        with self._lock:
            entry = self._cache.get(key)
            if entry and entry.is_valid():
                return entry.data
            elif entry:
                # Süresi dolmuş, sil
                del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Cache'e değer kaydeder"""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> None:
        """Cache'den değer siler"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Tüm cache'i temizler"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> None:
        """Süresi dolmuş cache entry'lerini temizler"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]


# Global cache instance
_cache_service = CacheService()

def get_cache() -> CacheService:
    """Global cache instance'ını döndürür"""
    return _cache_service

