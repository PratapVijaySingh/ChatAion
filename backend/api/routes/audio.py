from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import io
from core.audio_service import AudioService

logger = logging.getLogger(__name__)
router = APIRouter()

class AudioRequest(BaseModel):
    """Audio request model"""
    text: str
    voice_id: Optional[str] = None
    emotion: str = "neutral"
    model: str = "eleven_monolingual_v1"

class VoiceInfo(BaseModel):
    """Voice information model"""
    voice_id: str
    name: str
    category: str
    description: Optional[str] = None
    labels: Dict[str, str]

@router.post("/stt")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None)
):
    """Convert speech to text using OpenAI Whisper"""
    try:
        # Validate file type
        if not audio_file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Process speech to text
        result = await AudioService.speech_to_text(
            audio_data=audio_data,
            language=language,
            prompt=prompt
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Speech-to-text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(request: AudioRequest):
    """Convert text to speech using ElevenLabs"""
    try:
        # Generate audio
        audio_result = await AudioService.create_audio_response(
            text=request.text,
            voice_id=request.voice_id,
            emotion=request.emotion
        )
        
        # Return audio as streaming response
        audio_stream = io.BytesIO(audio_result["audio_data"])
        
        return StreamingResponse(
            audio_stream,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=response.wav",
                "X-Emotion": audio_result["emotion"]
            }
        )
        
    except Exception as e:
        logger.error(f"Text-to-speech error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices", response_model=List[VoiceInfo])
async def get_available_voices():
    """Get available ElevenLabs voices"""
    try:
        voices = await AudioService.get_available_voices()
        voice_list = []
        
        for voice_id, voice_data in voices.items():
            voice_list.append(VoiceInfo(
                voice_id=voice_id,
                name=voice_data.get("name", "Unknown"),
                category=voice_data.get("category", "Unknown"),
                description=voice_data.get("description"),
                labels=voice_data.get("labels", {})
            ))
        
        return voice_list
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_audio_emotion(
    audio_file: UploadFile = File(...)
):
    """Analyze audio to detect emotional content"""
    try:
        # Validate file type
        if not audio_file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Analyze audio emotion
        emotion_data = await AudioService.analyze_audio_emotion(audio_data)
        
        return emotion_data
        
    except Exception as e:
        logger.error(f"Audio emotion analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_audio(
    text: str = Form(...),
    voice_id: Optional[str] = Form(None),
    emotion: str = Form("neutral")
):
    """Stream text-to-speech audio"""
    try:
        # Generate audio
        audio_result = await AudioService.create_audio_response(
            text=text,
            voice_id=voice_id,
            emotion=emotion
        )
        
        # Return audio as streaming response
        audio_stream = io.BytesIO(audio_result["audio_data"])
        
        return StreamingResponse(
            audio_stream,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=stream.wav",
                "X-Emotion": audio_result["emotion"],
                "X-Voice-Settings": str(audio_result["voice_settings"])
            }
        )
        
    except Exception as e:
        logger.error(f"Audio streaming error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 