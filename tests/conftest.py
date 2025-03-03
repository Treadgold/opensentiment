import pytest
import json
import asyncio
from pathlib import Path
from opensentiment.url_analysis.extractor import URLExtractor
from opensentiment.processors.analysis_processor import AnalysisProcessor
from opensentiment.cache.analysis_cache import AnalysisCache

@pytest.fixture
def test_data():
    """Load test data from JSON file"""
    data_path = Path(__file__).parent / "test_data" / "analysis_samples.json"
    with open(data_path) as f:
        return json.load(f)

@pytest.fixture
async def url_extractor():
    """Create URL extractor instance"""
    async with URLExtractor() as extractor:
        yield extractor

@pytest.fixture
async def analysis_processor():
    """Create analysis processor instance"""
    processor = AnalysisProcessor()
    yield processor

@pytest.fixture
async def analysis_cache():
    """Create analysis cache instance with test configuration"""
    cache = AnalysisCache(redis_url="redis://localhost:6379/1")  # Use separate test DB
    yield cache
    await cache.clear()  # Cleanup after tests 