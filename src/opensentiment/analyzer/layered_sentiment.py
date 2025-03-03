from typing import Dict, Any, List
from .political_sentiment import PoliticalSentimentAnalyzer
from transformers import pipeline
import time

class LayeredSentimentAnalyzer:
    def __init__(self):
        # Primary analyzer for political sentiment
        self.political_analyzer = PoliticalSentimentAnalyzer()
        
        # Secondary analyzers for additional context
        self.emotion_analyzer = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=3
        )
        
        self.tone_analyzer = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

    async def analyze(self, content: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # First layer: Political Analysis
        political_results = await self.political_analyzer.analyze(content)
        
        # Second layer: Emotional Context
        emotion_results = await self._analyze_emotions(content)
        
        # Third layer: Overall Tone
        tone_results = await self._analyze_tone(content)
        
        # Combine all layers into comprehensive analysis
        return {
            "political_sentiment": political_results["political_sentiment"],
            "context": {
                "emotions": emotion_results,
                "tone": tone_results,
            },
            "metadata": {
                "text_length": len(content),
                "processing_time": time.time() - start_time,
                "analysis_version": "1.0"
            }
        }
    
    async def _analyze_emotions(self, content: str) -> Dict[str, Any]:
        try:
            emotions = self.emotion_analyzer(content)
            return {
                "primary_emotion": emotions[0]["label"],
                "confidence": emotions[0]["score"],
                "secondary_emotions": [
                    {"emotion": e["label"], "score": e["score"]}
                    for e in emotions[1:]
                ]
            }
        except Exception as e:
            return {"error": "Emotion analysis failed", "details": str(e)}
    
    async def _analyze_tone(self, content: str) -> Dict[str, Any]:
        try:
            tone = self.tone_analyzer(content)[0]
            return {
                "tone": tone["label"],
                "confidence": tone["score"]
            }
        except Exception as e:
            return {"error": "Tone analysis failed", "details": str(e)}

    async def get_analysis_summary(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis"""
        political = results["political_sentiment"]
        context = results["context"]
        
        summary = [
            f"Political Leaning: {political['label']} (Score: {political['score']:.1f}/100)",
            f"Emotional Context: {context['emotions']['primary_emotion']}",
            f"Overall Tone: {context['tone']['tone']}"
        ]
        
        return "\n".join(summary) 