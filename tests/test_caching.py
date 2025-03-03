import pytest
from time import sleep

@pytest.mark.asyncio
async def test_cache_operations(analysis_cache, test_data):
    # Test basic cache operations
    sample = test_data["text_samples"][0]
    result = {"test": "data"}
    
    # Set cache
    await analysis_cache.set(sample["content"], result)
    
    # Get from cache
    cached = await analysis_cache.get(sample["content"])
    assert cached == result
    
    # Test TTL
    sleep(1)  # Wait a bit
    assert await analysis_cache.get(sample["content"]) is not None
    
@pytest.mark.asyncio
async def test_cache_metrics(analysis_cache, test_data):
    sample = test_data["text_samples"][0]
    result = {"test": "data"}
    
    # First access should be a miss
    cached = await analysis_cache.get(sample["content"])
    assert cached is None
    
    # Set and get should result in a hit
    await analysis_cache.set(sample["content"], result)
    cached = await analysis_cache.get(sample["content"])
    assert cached is not None 