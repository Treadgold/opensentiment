from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge
import time

class AnalyzerMetrics:
    def __init__(self):
        # Cache metrics
        self.cache_hits = Counter(
            'analyzer_cache_hits_total',
            'Number of cache hits',
            ['cache_type']  # 'local' or 'redis'
        )
        self.cache_misses = Counter(
            'analyzer_cache_misses_total',
            'Number of cache misses',
            ['cache_type']
        )
        
        # Performance metrics
        self.processing_time = Histogram(
            'analyzer_processing_seconds',
            'Time spent processing analysis',
            ['analysis_type'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf'))
        )
        
        # System metrics
        self.active_analyses = Gauge(
            'analyzer_active_analyses',
            'Number of analyses currently being processed'
        )
        
        # Error metrics
        self.errors = Counter(
            'analyzer_errors_total',
            'Number of analysis errors',
            ['error_type']
        )
        
        # Content metrics
        self.content_length = Histogram(
            'analyzer_content_length_chars',
            'Length of analyzed content in characters',
            buckets=(100, 500, 1000, 5000, 10000, 50000)
        )

    async def record_cache_hit(self, cache_type: str):
        self.cache_hits.labels(cache_type=cache_type).inc()

    async def record_cache_miss(self, cache_type: str):
        self.cache_misses.labels(cache_type=cache_type).inc()

    @contextlib.asynccontextmanager
    async def track_processing_time(self, analysis_type: str):
        """Context manager to track processing time"""
        start_time = time.time()
        self.active_analyses.inc()
        try:
            yield
        finally:
            self.processing_time.labels(analysis_type=analysis_type).observe(
                time.time() - start_time
            )
            self.active_analyses.dec()

    async def record_error(self, error_type: str):
        self.errors.labels(error_type=error_type).inc()

    async def record_content_length(self, length: int):
        self.content_length.observe(length)

    def get_cache_hit_rate(self, cache_type: str) -> float:
        """Calculate cache hit rate"""
        hits = self.cache_hits.labels(cache_type=cache_type)._value.get()
        misses = self.cache_misses.labels(cache_type=cache_type)._value.get()
        total = hits + misses
        return hits / total if total > 0 else 0.0 