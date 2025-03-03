from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug_mode: bool = True
    database_url: str = "sqlite:///./test.db"  # Just for testing
    jwt_secret: str = "your-secret-key"  # Change in production!

    class Config:
        env_file = ".env" 