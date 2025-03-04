import pytest
import json
from opensentiment.analyzer.political_sentiment import PoliticalSentimentAnalyzer
from opensentiment.config.ollama_config import OllamaSettings
import aiohttp
from unittest.mock import patch, MagicMock

# Test settings
TEST_SETTINGS = OllamaSettings(
    OLLAMA_HOST="localhost",
    OLLAMA_PORT=11434,
    DEV_MODE=True,
    DEFAULT_MODEL="mistral"
)

# Sample mock responses
MOCK_COT_RESPONSE = {
    "response": json.dumps({
        "thought_process": [
            "Text discusses economic policies",
            "Uses terms associated with progressive ideology",
            "Emphasizes social welfare and regulation"
        ],
        "ideologies": {
            "primary": "progressive",
            "secondary": ["social democratic", "environmentalist"],
            "confidence": 0.85
        },
        "overall_confidence": 0.85
    })
}

MOCK_BIAS_SCORES = {
    "response": json.dumps({
        "political_spectrum": {"score": 25.0, "confidence": 0.85},
        "economic_policy": {"score": 20.0, "confidence": 0.9},
        "social_policy": {"score": 15.0, "confidence": 0.85},
        "institutional_trust": {"score": 60.0, "confidence": 0.75},
        "globalism_nationalism": {"score": 30.0, "confidence": 0.8}
    })
}

@pytest.fixture
async def analyzer():
    async with PoliticalSentimentAnalyzer(settings=TEST_SETTINGS) as analyzer:
        yield analyzer

@pytest.mark.asyncio
async def test_analyzer_initialization(analyzer):
    assert analyzer.settings.model_name == "mistral"
    assert analyzer.settings.api_url == "http://localhost:11434/api/generate"
    assert len(analyzer.bias_dimensions) == 5

@pytest.mark.asyncio
async def test_analyze_with_mock_responses(analyzer):
    # Sample text for analysis
    text = """We need strong government regulation of corporations and a robust social safety net. 
    Universal healthcare and free education should be fundamental rights."""
    
    # Mock the Ollama API responses
    with patch('aiohttp.ClientSession.post') as mock_post:
        # Configure mock to return different responses for different calls
        mock_post.side_effect = [
            MagicMock(
                __aenter__=MagicMock(return_value=MagicMock(
                    json=MagicMock(return_value=MOCK_COT_RESPONSE)
                ))
            ),
            MagicMock(
                __aenter__=MagicMock(return_value=MagicMock(
                    json=MagicMock(return_value=MOCK_BIAS_SCORES)
                ))
            ),
            # Add mock responses for narrative and entity analysis
            MagicMock(
                __aenter__=MagicMock(return_value=MagicMock(
                    json=MagicMock(return_value={"response": "{}"})
                ))
            ),
            MagicMock(
                __aenter__=MagicMock(return_value=MagicMock(
                    json=MagicMock(return_value={"response": "{}"})
                ))
            )
        ]
        
        result = await analyzer.analyze(text)
        
        # Verify the structure and content of the result
        assert "bias_scores" in result
        assert "confidence_scores" in result
        assert "ideology_classifications" in result
        assert "narrative_markers" in result
        assert "topic_analysis" in result
        assert "model_version" in result
        assert "analysis_version" in result
        
        # Verify specific values
        assert result["bias_scores"]["political_spectrum"]["score"] == 25.0
        assert result["ideology_classifications"]["primary"] == "progressive"
        assert len(result["ideology_classifications"]["secondary"]) == 2
        assert result["processing_metadata"]["model"] == "mistral"

@pytest.mark.asyncio
async def test_error_handling(analyzer):
    # Test with invalid response
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.side_effect = aiohttp.ClientError("Connection failed")
        
        result = await analyzer.analyze("test content")
        
        assert "error" in result
        assert result["model_version"] == "mistral"
        assert "error_type" in result["processing_metadata"]
        assert result["processing_metadata"]["error_type"] == "ClientError"

@pytest.mark.asyncio
async def test_bias_dimensions_coverage(analyzer):
    # Verify all bias dimensions are properly initialized
    expected_dimensions = {
        "political_spectrum",
        "economic_policy",
        "social_policy",
        "institutional_trust",
        "globalism_nationalism"
    }
    
    assert set(analyzer.bias_dimensions.keys()) == expected_dimensions
    
    # Verify each dimension has proper scale and description
    for dimension in analyzer.bias_dimensions.values():
        assert "description" in dimension
        assert "scale" in dimension
        assert len(dimension["scale"]) == 2
        assert dimension["scale"][0] == 0
        assert dimension["scale"][1] == 100

@pytest.mark.asyncio
async def test_request_parameters(analyzer):
    params = analyzer.settings.get_request_params("test prompt")
    
    assert params["model"] == "mistral"
    assert not params["stream"]
    assert "options" in params
    assert "temperature" in params["options"]
    assert "top_p" in params["options"]
    assert "num_predict" in params["options"] 