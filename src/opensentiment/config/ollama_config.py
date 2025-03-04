from typing import Dict, Any
from pydantic import BaseSettings

class OllamaSettings(BaseSettings):
    """Ollama configuration settings"""
    
    # Base configuration
    OLLAMA_HOST: str = "localhost"
    OLLAMA_PORT: int = 11434
    OLLAMA_URL: str = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
    
    # Model configuration
    DEFAULT_MODEL: str = "mistral"  # Default model for development
    PRODUCTION_MODEL: str = "llama2"  # Default model for production
    
    # Request configuration
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    
    # Timeout settings
    REQUEST_TIMEOUT: int = 30  # seconds
    
    # Development settings
    DEV_MODE: bool = True
    
    @property
    def model_name(self) -> str:
        """Get the appropriate model name based on environment"""
        return self.DEFAULT_MODEL if self.DEV_MODE else self.PRODUCTION_MODEL
    
    @property
    def api_url(self) -> str:
        """Get the full API URL"""
        return self.OLLAMA_URL
    
    def get_request_params(self, prompt: str) -> Dict[str, Any]:
        """Get the parameters for an Ollama API request"""
        return {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.TEMPERATURE,
                "top_p": self.TOP_P,
                "num_predict": self.MAX_TOKENS
            }
        }
    
    class Config:
        env_prefix = "OLLAMA_"
        case_sensitive = True 