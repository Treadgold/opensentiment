from typing import Dict, Any, List, Tuple
from .base import BaseAnalyzer
import aiohttp
import json
import time
from datetime import datetime
from ..config.ollama_config import OllamaSettings

class PoliticalSentimentAnalyzer(BaseAnalyzer):
    def __init__(self, settings: OllamaSettings = None):
        self.settings = settings or OllamaSettings()
        self.session = None
        
        # Define bias dimensions based on our schema
        self.bias_dimensions = {
            "political_spectrum": {
                "description": "Traditional left-right political spectrum",
                "scale": (0, 100)  # 0 = far left, 100 = far right
            },
            "economic_policy": {
                "description": "Economic policy preferences",
                "scale": (0, 100)  # 0 = state control, 100 = free market
            },
            "social_policy": {
                "description": "Social policy preferences",
                "scale": (0, 100)  # 0 = progressive, 100 = conservative
            },
            "institutional_trust": {
                "description": "Trust in institutions",
                "scale": (0, 100)  # 0 = anti-establishment, 100 = pro-establishment
            },
            "globalism_nationalism": {
                "description": "Global vs nationalist orientation",
                "scale": (0, 100)  # 0 = globalist, 100 = nationalist
            }
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def analyze(self, content: str) -> Dict[str, Any]:
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        start_time = time.time()
        
        try:
            # Step 1: Initial chain-of-thought analysis
            cot_analysis = await self._perform_cot_analysis(content)
            
            # Step 2: Extract structured scores from the analysis
            bias_scores = await self._extract_bias_scores(cot_analysis)
            
            # Step 3: Analyze narrative patterns and rhetoric
            narrative_analysis = await self._analyze_narratives(content, cot_analysis)
            
            # Step 4: Entity and topic analysis
            entity_analysis = await self._analyze_entities(content)
            
            return {
                "bias_scores": bias_scores,
                "confidence_scores": {
                    dim: score["confidence"] 
                    for dim, score in bias_scores.items()
                },
                "ideology_classifications": cot_analysis["ideologies"],
                "narrative_markers": narrative_analysis["markers"],
                "topic_analysis": {
                    "main_topics": entity_analysis["topics"],
                    "keywords": entity_analysis["keywords"]
                },
                "entity_sentiment": entity_analysis["entities"],
                "rhetoric_analysis": narrative_analysis["rhetoric"],
                "temporal_context": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_window": "current"
                },
                "model_version": self.settings.model_name,
                "analysis_version": "2.0",
                "processing_metadata": {
                    "processing_time": time.time() - start_time,
                    "model": self.settings.model_name,
                    "confidence": cot_analysis["overall_confidence"]
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "model_version": self.settings.model_name,
                "analysis_version": "2.0",
                "processing_metadata": {
                    "processing_time": time.time() - start_time,
                    "error_type": type(e).__name__
                }
            }

    async def _perform_cot_analysis(self, content: str) -> Dict[str, Any]:
        """Perform chain-of-thought analysis using Ollama"""
        prompt = f"""Analyze the political bias and ideology in the following text. Think step by step:

1. First, identify the main political topics and themes
2. Analyze the language and rhetoric used
3. Identify any ideological markers or positions
4. Consider the context and implications
5. Evaluate the overall political leaning

Text: {content}

Provide your analysis in JSON format with the following structure:
{{
    "thought_process": [list of step-by-step thoughts],
    "ideologies": {{
        "primary": "main ideology",
        "secondary": ["other detected ideologies"],
        "confidence": float
    }},
    "overall_confidence": float
}}"""

        async with self.session.post(
            self.settings.api_url,
            json=self.settings.get_request_params(prompt),
            timeout=self.settings.REQUEST_TIMEOUT
        ) as response:
            result = await response.json()
            try:
                return json.loads(result["response"])
            except (json.JSONDecodeError, KeyError):
                return {
                    "thought_process": [],
                    "ideologies": {
                        "primary": "unknown",
                        "secondary": [],
                        "confidence": 0.0
                    },
                    "overall_confidence": 0.0
                }

    async def _extract_bias_scores(self, cot_analysis: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Extract numerical scores for each bias dimension based on the analysis"""
        prompt = f"""Based on this political analysis, provide numerical scores for each bias dimension.
Analysis: {json.dumps(cot_analysis)}

Provide scores in JSON format for each dimension (0-100 scale):
{{
    "dimension_name": {{
        "score": float,
        "confidence": float
    }}
}}"""

        async with self.session.post(
            self.settings.api_url,
            json=self.settings.get_request_params(prompt),
            timeout=self.settings.REQUEST_TIMEOUT
        ) as response:
            result = await response.json()
            try:
                return json.loads(result["response"])
            except (json.JSONDecodeError, KeyError):
                return {
                    dim: {"score": 50.0, "confidence": 0.0}
                    for dim in self.bias_dimensions.keys()
                }

    async def _analyze_narratives(self, content: str, cot_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze narrative patterns and rhetorical devices"""
        prompt = f"""Analyze the narrative patterns and rhetorical devices in this text:
Text: {content}

Previous analysis: {json.dumps(cot_analysis)}

Provide analysis in JSON format:
{{
    "markers": {{
        "narrative_patterns": [list of patterns],
        "framing_devices": [list of devices],
        "emotional_appeals": [list of appeals]
    }},
    "rhetoric": {{
        "devices": [list of rhetorical devices],
        "style": string,
        "persuasion_techniques": [list of techniques]
    }}
}}"""

        async with self.session.post(
            self.settings.api_url,
            json=self.settings.get_request_params(prompt),
            timeout=self.settings.REQUEST_TIMEOUT
        ) as response:
            result = await response.json()
            try:
                return json.loads(result["response"])
            except (json.JSONDecodeError, KeyError):
                return {
                    "markers": {
                        "narrative_patterns": [],
                        "framing_devices": [],
                        "emotional_appeals": []
                    },
                    "rhetoric": {
                        "devices": [],
                        "style": "unknown",
                        "persuasion_techniques": []
                    }
                }

    async def _analyze_entities(self, content: str) -> Dict[str, Any]:
        """Analyze entities, topics, and keywords"""
        prompt = f"""Analyze the entities, topics, and keywords in this text:
Text: {content}

Provide analysis in JSON format:
{{
    "entities": {{
        "people": [list of people with sentiment],
        "organizations": [list of organizations with sentiment],
        "concepts": [list of concepts with sentiment]
    }},
    "topics": [list of main topics],
    "keywords": [list of important keywords]
}}"""

        async with self.session.post(
            self.settings.api_url,
            json=self.settings.get_request_params(prompt),
            timeout=self.settings.REQUEST_TIMEOUT
        ) as response:
            result = await response.json()
            try:
                return json.loads(result["response"])
            except (json.JSONDecodeError, KeyError):
                return {
                    "entities": {
                        "people": [],
                        "organizations": [],
                        "concepts": []
                    },
                    "topics": [],
                    "keywords": []
                } 