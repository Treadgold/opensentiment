from typing import Dict, List, Any
from .base import BaseModel, ModelConfig

class ModelRegistry:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.models: Dict[str, BaseModel] = {}
        
    async def register_model(self, model_id: str, model: BaseModel) -> None:
        """Register a new model in the registry"""
        await model.validate()
        self.models[model_id] = model
        
    async def load_models(self) -> None:
        """Load all registered models"""
        for model in self.models.values():
            await model.load()
            
    async def get_model(self, model_id: str) -> BaseModel:
        """Get a specific model by ID"""
        if model_id not in self.models:
            raise KeyError(f"Model {model_id} not found")
        return self.models[model_id]
        
    async def list_models(self) -> List[ModelConfig]:
        """List all available models"""
        return [model.config for model in self.models.values()] 