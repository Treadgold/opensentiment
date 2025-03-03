from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
import uvicorn
import logging
from datetime import datetime
import asyncio
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import local modules
from .config import Settings
from .models import ModelRegistry
from .database import Database
from .auth import get_current_user, User
from .processors import ContentProcessor, SourceAnalyzer
from .schemas import (
    AnalysisRequest,
    AnalysisResponse,
    SourceAnalysis,
    ModelComparison,
    ContentMetadata
)
from opensentiment.processors.analysis_processor import AnalysisProcessor

# Define response models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AnalysisRequest(BaseModel):
    content: Optional[str] = None
    url: Optional[HttpUrl] = None
    models: Optional[List[str]] = Field(default_factory=list)
    
    @property
    def has_valid_input(self) -> bool:
        return bool(self.content) != bool(self.url)  # XOR - only one should be provided

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OpenSentiment API",
    description="Open-source sentiment and bias analysis API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Initialize components
    settings = Settings()
    db = Database(settings)
    model_registry = ModelRegistry(settings)
    
    # Try to import analyzers, use mock implementations if not available
    try:
        from opensentiment import SentimentAnalyzer, BiasAnalyzer, CredibilityAnalyzer
        sentiment_analyzer = SentimentAnalyzer()
        bias_analyzer = BiasAnalyzer()
        credibility_analyzer = CredibilityAnalyzer()
        logger.info("Using OpenSentiment analyzers")
    except ImportError:
        logger.warning("OpenSentiment package not found, using mock analyzers")
        
        class MockAnalyzer:
            async def analyze(self, content: str) -> Dict[str, Any]:
                return {
                    "score": 0.75,
                    "confidence": 0.85,
                    "details": {
                        "positive": 0.75,
                        "negative": 0.15,
                        "neutral": 0.10
                    },
                    "status": "mock_analysis",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        sentiment_analyzer = MockAnalyzer()
        bias_analyzer = MockAnalyzer()
        credibility_analyzer = MockAnalyzer()
    
    content_processor = ContentProcessor(model_registry)
    source_analyzer = SourceAnalyzer()
    
    # Initialize processor
    analysis_processor = AnalysisProcessor(max_workers=4)
    
except Exception as e:
    logger.critical(f"Failed to initialize components: {str(e)}")
    raise

@app.on_event("startup")
async def startup_event():
    try:
        await db.connect()
        await model_registry.load_models()
        logger.info("Application started successfully")
    except Exception as e:
        logger.critical(f"Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await db.disconnect()
        logger.info("Application shut down successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

@app.post("/v1/analyze", response_model=AnalysisResponse)
async def analyze_content(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        if not request.has_valid_input:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either content or URL must be provided, but not both"
            )

        # Create analysis job
        job_id = await db.create_job(current_user.id)
        
        # Add analysis task to background processing
        background_tasks.add_task(
            process_analysis,
            job_id=job_id,
            request=request,
            user_id=current_user.id
        )
        
        return AnalysisResponse(
            job_id=job_id,
            status="pending",
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during analysis request"
        )

@app.get("/v1/analysis/{job_id}", response_model=AnalysisResponse)
async def get_analysis_results(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        job = await db.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis job {job_id} not found"
            )
            
        if job.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this analysis"
            )
        
        # Convert the job data to match AnalysisResponse model
        response = AnalysisResponse(
            job_id=job_id,
            status=job.get("status", "unknown"),
            created_at=job.get("created_at", datetime.utcnow()),
            completed_at=job.get("completed_at"),
            results=job.get("results"),
            error=job.get("error")
        )
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred"
        ).dict()
    )

async def process_analysis(job_id: str, request: AnalysisRequest, user_id: str):
    """Background task to process the analysis"""
    try:
        await db.update_job_status(job_id, "processing")
        
        content = request.content if request.content else "URL content placeholder"
        
        # Use the new processor
        results = await analysis_processor.process_content(content)
        
        await db.update_job_results(job_id, results)
        await db.update_job_status(job_id, "completed")
        
    except Exception as e:
        logger.error(f"Analysis processing failed for job {job_id}: {str(e)}")
        await db.update_job_status(job_id, "failed", str(e))

@app.get("/v1/source/{domain}", response_model=SourceAnalysis)
async def analyze_source(
    domain: str,
    current_user: User = Depends(get_current_user)
):
    """Get source credibility and bias analysis"""
    try:
        source_info = await source_analyzer.analyze_domain(domain)
        return source_info
    except Exception as e:
        logger.error(f"Error analyzing source: {str(e)}")
        raise HTTPException(status_code=500, detail="Source analysis failed")

@app.post("/v1/models/compare", response_model=ModelComparison)
async def compare_models(
    content: AnalysisRequest,
    model_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """Compare analysis results across different models"""
    try:
        comparison = await model_registry.compare_models(content, model_ids)
        return comparison
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}")
        raise HTTPException(status_code=500, detail="Model comparison failed")

@app.get("/v1/models", response_model=List[Dict[str, Any]])
async def list_models(current_user: User = Depends(get_current_user)):
    """List available analysis models"""
    try:
        models = await model_registry.list_models()
        return models
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list models")

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug_mode,
        log_level="debug" if settings.debug_mode else "info"
    ) 