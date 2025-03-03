import pytest
from opensentiment.analyzer.political_sentiment import PoliticalSentimentAnalyzer

@pytest.mark.asyncio
async def test_political_sentiment_analysis(test_data):
    analyzer = PoliticalSentimentAnalyzer()
    
    for sample in test_data["text_samples"]:
        result = await analyzer.analyze(sample["content"])
        
        # Check basic structure
        assert "political_sentiment" in result
        assert "score" in result["political_sentiment"]
        assert "label" in result["political_sentiment"]
        
        # Check expected values
        expected = sample["expected"]["political_sentiment"]
        actual = result["political_sentiment"]
        
        # Allow for some variance in scores
        assert abs(expected["score"] - actual["score"]) <= 10
        assert expected["label"] == actual["label"]
        
        # Check confidence
        assert "confidence" in actual
        assert 0 <= actual["confidence"] <= 1

@pytest.mark.asyncio
async def test_edge_cases(test_data):
    analyzer = PoliticalSentimentAnalyzer()
    
    for case in test_data["edge_cases"]:
        result = await analyzer.analyze(case["content"])
        expected = case["expected"]["political_sentiment"]
        
        if "confidence" in expected:
            if expected["confidence"] == "<0.5":
                assert result["political_sentiment"]["confidence"] < 0.5 