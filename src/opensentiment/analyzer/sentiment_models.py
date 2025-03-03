from typing import Dict, Any, List
from transformers import (
    AutoModelForSequenceClassification, 
    AutoTokenizer,
    pipeline
)
import torch
import numpy as np

class SentimentModelEnsemble:
    def __init__(self):
        self.models = {
            "distilbert": {
                "name": "distilbert-base-uncased-finetuned-sst-2-english",
                "weight": 0.4
            },
            "roberta": {
                "name": "roberta-base-sentiment",
                "weight": 0.4
            },
            "vader": {
                "name": "vader",
                "weight": 0.2  # Rule-based system as backup
            }
        }
        
        self.tokenizers = {}
        self.model_instances = {}
        
    async def load(self):
        for model_id, config in self.models.items():
            if model_id != "vader":
                self.tokenizers[model_id] = AutoTokenizer.from_pretrained(config["name"])
                self.model_instances[model_id] = AutoModelForSequenceClassification.from_pretrained(config["name"])
            else:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self.model_instances[model_id] = SentimentIntensityAnalyzer() 