from typing import Dict, Any, Optional
import hashlib
import json
from datetime import datetime, timedelta
import aioredis
import asyncio
from functools import lru_cache
from ..metrics.analyzer_metrics import AnalyzerMetrics

class AnalysisCache:
    def __init__(self, redis_url: str = "redis://localhost", ttl: int = 86400):
        self.redis = aioredis.from_url(redis_url)
        self.ttl = ttl  # Cache TTL in seconds (default 24 hours)
        self.local_cache = lru_cache(maxsize=1000)(self._get_local_cache)
        self.metrics = AnalyzerMetrics()
        
    def _generate_hash(self, content: str) -> str:
        """Generate a unique hash for the content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get(self, content: str) -> Optional[Dict[str, Any]]:
        """Get analysis results from cache"""
        content_hash = self._generate_hash(content)
        
        # Try local cache
        local_result = self.local_cache(content_hash)
        if local_result:
            await self.metrics.record_cache_hit('local')
            return local_result
        await self.metrics.record_cache_miss('local')
            
        # Try Redis cache
        cached = await self.redis.get(content_hash)
        if cached:
            result = json.loads(cached)
            self.local_cache(content_hash, result)
            await self.metrics.record_cache_hit('redis')
            return result
        await self.metrics.record_cache_miss('redis')
            
        return None
        
    async def set(self, content: str, results: Dict[str, Any]) -> None:
        """Store analysis results in cache"""
        content_hash = self._generate_hash(content)
        
        # Add timestamp for cache invalidation
        results["cache_timestamp"] = datetime.utcnow().isoformat()
        
        # Store in Redis
        await self.redis.set(
            content_hash,
            json.dumps(results),
            ex=self.ttl
        )
        
        # Update local cache
        self.local_cache(content_hash, results)
        
    def _get_local_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Local cache implementation"""
        return None  # Handled by lru_cache decorator
        
    async def clear(self) -> None:
        """Clear all caches"""
        await self.redis.flushdb()
        self.local_cache.cache_clear() 