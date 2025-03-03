from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ModelConfig(BaseModel):
    name: str
    version: str
    type: str
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class BaseModel(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config
        
    @abstractmethod
    async def load(self) -> None:
        """Load the model and its resources"""
        pass
        
    @abstractmethod
    async def predict(self, input_data: Any) -> Dict[str, Any]:
        """Make predictions using the model"""
        pass
        
    @abstractmethod
    async def validate(self) -> bool:
        """Validate model performance"""
        pass 