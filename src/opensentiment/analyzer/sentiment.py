from typing import Dict, Any, List
from .sentiment_models import SentimentModelEnsemble
from .base import BaseAnalyzer
from transformers import pipeline

class SentimentAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.ensemble = SentimentModelEnsemble()
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=3
        )
        
    async def analyze(self, content: str) -> Dict[str, Any]:
        # Get ensemble predictions
        ensemble_results = await self._get_ensemble_predictions(content)
        
        # Get emotion analysis
        emotions = await self._get_emotion_analysis(content)
        
        # Combine results
        return {
            "sentiment": {
                "score": ensemble_results["weighted_score"],
                "confidence": ensemble_results["confidence"],
                "label": ensemble_results["label"]
            },
            "emotions": emotions,
            "model_details": ensemble_results["model_scores"],
            "metadata": {
                "text_length": len(content),
                "language": "en",  # Add language detection later
                "processing_time": ensemble_results["processing_time"]
            }
        }
    
    async def batch_analyze(self, contents: list[str]) -> list[Dict[str, Any]]:
        results = []
        for content in contents:
            results.append(await self.analyze(content))
        return results 