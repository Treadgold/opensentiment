from typing import Dict, Any, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..cache.analysis_cache import AnalysisCache
from ..analyzer.layered_sentiment import LayeredSentimentAnalyzer
from ..metrics.analyzer_metrics import AnalyzerMetrics

class AnalysisProcessor:
    def __init__(self, max_workers: int = 4):
        self.cache = AnalysisCache()
        self.analyzer = LayeredSentimentAnalyzer()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.metrics = AnalyzerMetrics()
        
    async def process_content(self, content: str) -> Dict[str, Any]:
        await self.metrics.record_content_length(len(content))
        
        try:
            async with self.metrics.track_processing_time('full_analysis'):
                # Check cache first
                cached_result = await self.cache.get(content)
                if cached_result:
                    return cached_result
                    
                # Process new content
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    self._process_single_content,
                    content
                )
                
                # Cache the result
                await self.cache.set(content, result)
                return result
                
        except Exception as e:
            await self.metrics.record_error(type(e).__name__)
            raise
        
    async def process_batch(self, contents: List[str]) -> List[Dict[str, Any]]:
        tasks = []
        for content in contents:
            tasks.append(self.process_content(content))
        return await asyncio.gather(*tasks)
    
    def _process_single_content(self, content: str) -> Dict[str, Any]:
        """Synchronous processing for thread pool"""
        return asyncio.run(self.analyzer.analyze(content)) 