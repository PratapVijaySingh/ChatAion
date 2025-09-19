from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

from api.routes import chat, audio, animation, avatar
from core.config import settings
from core.llm_service import LLMService
from core.audio_service import AudioService
from core.animation_service import AnimationService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Virtual Human API",
    description="AI-powered virtual human system with real-time speech and animation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(animation.router, prefix="/api/animation", tags=["animation"])
app.include_router(avatar.router, prefix="/api/avatar", tags=["avatar"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Virtual Human API...")
    
    # Initialize core services
    try:
        await LLMService.initialize()
        await AudioService.initialize()
        await AnimationService.initialize()
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Virtual Human API...")
    
    # Cleanup services
    try:
        await LLMService.cleanup()
        await AudioService.cleanup()
        await AnimationService.cleanup()
        logger.info("All services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Virtual Human API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "llm": await LLMService.is_healthy(),
            "audio": await AudioService.is_healthy(),
            "animation": await AnimationService.is_healthy()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 