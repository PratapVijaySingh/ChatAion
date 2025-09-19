"""
Virtual Human API - Main Application
A FastAPI-based backend for AI-powered virtual human interactions
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.config import settings
from core.llm_service import LLMService
from core.audio_service import AudioService
from core.animation_service import AnimationService

# Import API routers
from api.routes import chat, audio, animation, avatar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
llm_service = None
audio_service = None
animation_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("Starting Virtual Human API...")
    try:
        # Initialize services with graceful fallback
        global llm_service, audio_service, animation_service
        
        # Try to initialize LLM service
        try:
            await LLMService.initialize()
            llm_service = LLMService
            logger.info("LLM service initialized successfully")
        except Exception as e:
            logger.warning(f"LLM service failed to initialize: {e}")
            logger.info("LLM service will run in demo mode")
            llm_service = None
        
        # Try to initialize Audio service
        try:
            await AudioService.initialize()
            audio_service = AudioService
            logger.info("Audio service initialized successfully")
        except Exception as e:
            logger.warning(f"Audio service failed to initialize: {e}")
            logger.info("Audio service will run in demo mode")
            audio_service = None
        
        # Try to initialize Animation service
        try:
            await AnimationService.initialize()
            animation_service = AnimationService
            logger.info("Animation service initialized successfully")
        except Exception as e:
            logger.warning(f"Animation service failed to initialize: {e}")
            logger.info("Animation service will run in demo mode")
            animation_service = None
        
        logger.info("Virtual Human API startup completed")
        
    except Exception as e:
        logger.error(f"Critical startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Virtual Human API...")
    try:
        if llm_service:
            await LLMService.cleanup()
        if audio_service:
            await AudioService.cleanup()
        if animation_service:
            await AnimationService.cleanup()
        logger.info("All services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Create FastAPI app
app = FastAPI(
    title="Virtual Human API",
    description="AI-powered virtual human interaction system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(animation.router, prefix="/api/animation", tags=["animation"])
app.include_router(avatar.router, prefix="/api/avatar", tags=["avatar"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Virtual Human API",
        "version": "1.0.0",
        "status": "running",
        "services": {
            "llm": "available" if llm_service else "demo_mode",
            "audio": "available" if audio_service else "demo_mode",
            "animation": "available" if animation_service else "demo_mode"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "llm": "healthy" if llm_service and LLMService.is_healthy() else "unavailable",
            "audio": "healthy" if audio_service and AudioService.is_healthy() else "unavailable",
            "animation": "healthy" if animation_service and AnimationService.is_healthy() else "unavailable"
        }
    }

@app.get("/api/status")
async def api_status():
    """Detailed API status"""
    return {
        "api": "Virtual Human API",
        "version": "1.0.0",
        "status": "running",
        "services": {
            "llm": {
                "status": "available" if llm_service else "demo_mode",
                "health": "healthy" if llm_service and LLMService.is_healthy() else "unavailable"
            },
            "audio": {
                "status": "available" if audio_service else "demo_mode",
                "health": "healthy" if audio_service and AudioService.is_healthy() else "unavailable"
            },
            "animation": {
                "status": "available" if animation_service else "demo_mode",
                "health": "healthy" if animation_service and AnimationService.is_healthy() else "unavailable"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True
    ) 