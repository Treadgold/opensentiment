from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAnalyzer(ABC):
    """Base class for all analyzers"""
    
    @abstractmethod
    async def analyze(self, content: str) -> Dict[str, Any]:
        """Perform analysis on content"""
        pass

    @abstractmethod
    async def batch_analyze(self, contents: list[str]) -> list[Dict[str, Any]]:
        """Perform batch analysis on multiple content items"""
        pass 