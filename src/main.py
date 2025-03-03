import uvicorn
from api.config import Settings

if __name__ == "__main__":
    settings = Settings()
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug_mode
    ) 