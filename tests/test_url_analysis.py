import pytest
from opensentiment.url_analysis.extractor import URLExtractor

@pytest.mark.asyncio
async def test_url_content_extraction(url_extractor, test_data):
    for sample in test_data["url_samples"]:
        result = await url_extractor.extract(sample["url"])
        
        assert result["domain"] == sample["expected"]["domain"]
        assert result["is_article"] == sample["expected"]["is_article"]
        assert "content" in result
        assert "metadata" in result
        
@pytest.mark.asyncio
async def test_duplicate_detection(url_extractor, test_data):
    results = []
    for sample in test_data["duplicate_detection"]:
        result = await url_extractor.extract(sample["url"])
        results.append(result)
        
        if sample["duplicate_of"]:
            # Find original content
            original = next(r for r in results if r["url"] == sample["duplicate_of"])
            assert result["content_hash"] == original["content_hash"] 