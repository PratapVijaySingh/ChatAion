"""
Audio API routes for Virtual Human
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, Optional
import logging

from core.audio_service import AudioService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Convert speech to text"""
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Process with audio service
        result = await AudioService.speech_to_text(audio_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in speech to text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(request_data: Dict[str, Any]):
    """Convert text to speech"""
    try:
        text = request_data.get("text", "")
        voice_id = request_data.get("voice_id")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Generate speech
        result = await AudioService.text_to_speech(text, voice_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in text to speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices")
async def get_available_voices():
    """Get available voices"""
    try:
        voices = AudioService.get_available_voices()
        return {"voices": voices}
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_audio_emotion(audio_file: UploadFile = File(...)):
    """Analyze audio for emotion"""
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Analyze emotion
        result = await AudioService.analyze_audio_emotion(audio_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing audio emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def process_audio_stream(audio_data: bytes):
    """Process streaming audio data"""
    try:
        result = await AudioService.process_audio_stream(audio_data)
        return result
        
    except Exception as e:
        logger.error(f"Error processing audio stream: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 