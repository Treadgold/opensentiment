from typing import Dict, Any, List, Tuple
from .base import BaseAnalyzer
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import time

class PoliticalSentimentAnalyzer(BaseAnalyzer):
    def __init__(self):
        # Initialize with a model fine-tuned for political classification
        self.model_name = "bert-base-uncased"  # We'll need to fine-tune this
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=3  # Left, Center, Right
        )
        
        # Political keywords and their weights for rule-based backup
        self.political_indicators = {
            "left": ["progressive", "socialist", "liberal", "welfare", "regulation"],
            "right": ["conservative", "free market", "traditional", "deregulation"],
            "center": ["moderate", "bipartisan", "compromise", "balanced"]
        }
        
    async def analyze(self, content: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # Get model prediction
        model_score = await self._get_model_prediction(content)
        
        # Get rule-based backup score
        rule_score = await self._get_rule_based_score(content)
        
        # Combine scores (weighted average)
        final_score = self._combine_scores(model_score, rule_score)
        
        # Map to 1-100 scale
        scaled_score = self._scale_score(final_score)
        
        return {
            "political_sentiment": {
                "score": scaled_score,
                "label": self._get_label(scaled_score),
                "confidence": float(model_score[1]),  # Confidence from model
            },
            "details": {
                "model_score": float(model_score[0]),
                "rule_based_score": float(rule_score),
                "processing_time": time.time() - start_time
            }
        }

    def _get_label(self, score: float) -> str:
        if score < 40:
            return "LEFT"
        elif score > 60:
            return "RIGHT"
        return "CENTER"

    async def _get_model_prediction(self, content: str) -> Tuple[float, float]:
        # Placeholder for actual model prediction
        # Returns (score, confidence)
        return 50.0, 0.8

    async def _get_rule_based_score(self, content: str) -> float:
        # Simple rule-based scoring
        content = content.lower()
        left_score = sum(word in content for word in self.political_indicators["left"])
        right_score = sum(word in content for word in self.political_indicators["right"])
        
        if left_score == right_score:
            return 50.0
        
        total = left_score + right_score
        if total == 0:
            return 50.0
            
        return (right_score / total) * 100

    def _combine_scores(self, model_score: Tuple[float, float], rule_score: float) -> float:
        model_weight = 0.8
        rule_weight = 0.2
        return (model_score[0] * model_weight) + (rule_score * rule_weight)

    def _scale_score(self, score: float) -> float:
        # Ensure score is between 1 and 100
        return max(1.0, min(100.0, score)) 