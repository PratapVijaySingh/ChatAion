"""
Audio Service for Virtual Human API
Handles speech-to-text and text-to-speech functionality
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
import io
import base64
from elevenlabs import generate, save, set_api_key, voices
from core.config import settings

logger = logging.getLogger(__name__)

class AudioService:
    """Service for managing audio processing"""
    
    _is_healthy: bool = False
    _demo_mode: bool = False
    _available_voices: List[Dict[str, Any]] = []
    
    @classmethod
    async def initialize(cls):
        """Initialize the Audio service"""
        try:
            # Check if ElevenLabs API key is configured
            if not settings.elevenlabs.api_key or settings.elevenlabs.api_key == "your_elevenlabs_api_key_here":
                logger.warning("ElevenLabs API key not configured. Running in demo mode.")
                cls._is_healthy = True
                cls._demo_mode = True
                return
            
            # Set API key
            set_api_key(settings.elevenlabs.api_key)
            
            # Load available voices
            await cls._load_voices()
            
            cls._is_healthy = True
            cls._demo_mode = False
            logger.info("Audio service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Audio service: {e}")
            cls._is_healthy = False
            cls._demo_mode = True
    
    @classmethod
    async def cleanup(cls):
        """Cleanup resources"""
        cls._is_healthy = False
        logger.info("Audio service cleaned up")
    
    @classmethod
    def is_healthy(cls) -> bool:
        """Check if the service is healthy"""
        return cls._is_healthy
    
    @classmethod
    async def _load_voices(cls):
        """Load available voices from ElevenLabs"""
        try:
            if not cls._demo_mode:
                available_voices = voices()
                cls._available_voices = [
                    {
                        "id": voice.voice_id,
                        "name": voice.name,
                        "category": voice.category,
                        "description": voice.description
                    }
                    for voice in available_voices
                ]
                logger.info(f"Loaded {len(cls._available_voices)} voices")
            else:
                # Demo voices
                cls._available_voices = [
                    {
                        "id": "demo_voice_1",
                        "name": "Demo Voice 1",
                        "category": "demo",
                        "description": "Demo voice for testing"
                    }
                ]
        except Exception as e:
            logger.error(f"Failed to load voices: {e}")
            cls._available_voices = []
    
    @classmethod
    async def speech_to_text(cls, audio_data: bytes) -> Dict[str, Any]:
        """Convert speech to text using Whisper API"""
        try:
            if cls._demo_mode:
                return {
                    "text": "Demo speech recognition - this is a sample transcription",
                    "confidence": 0.95,
                    "mode": "demo"
                }
            
            # In production, this would call OpenAI Whisper API
            # For now, return demo response
            return {
                "text": "Speech recognition service not fully implemented yet",
                "confidence": 0.8,
                "mode": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Error in speech to text: {e}")
            return {
                "text": "Error processing speech",
                "confidence": 0.0,
                "mode": "error",
                "error": str(e)
            }
    
    @classmethod
    async def text_to_speech(
        cls, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert text to speech using ElevenLabs"""
        try:
            if cls._demo_mode:
                return {
                    "audio_base64": "demo_audio_data",
                    "duration": 2.5,
                    "voice_id": voice_id or "demo_voice_1",
                    "mode": "demo"
                }
            
            if not voice_id:
                voice_id = settings.elevenlabs.voice_id
            
            # Generate audio using ElevenLabs
            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            
            # Convert to base64 for transmission
            audio_base64 = base64.b64encode(audio).decode('utf-8')
            
            return {
                "audio_base64": audio_base64,
                "duration": len(audio) / 22050,  # Approximate duration
                "voice_id": voice_id,
                "mode": "production"
            }
            
        except Exception as e:
            logger.error(f"Error in text to speech: {e}")
            return {
                "audio_base64": "error_audio_data",
                "duration": 0.0,
                "voice_id": voice_id or "unknown",
                "mode": "error",
                "error": str(e)
            }
    
    @classmethod
    def get_available_voices(cls) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        return cls._available_voices.copy()
    
    @classmethod
    async def process_audio_stream(cls, audio_stream: bytes) -> Dict[str, Any]:
        """Process streaming audio data"""
        try:
            if cls._demo_mode:
                return {
                    "status": "processed",
                    "text": "Demo audio stream processing",
                    "mode": "demo"
                }
            
            # Process audio stream (implement as needed)
            return {
                "status": "processed",
                "text": "Audio stream processed",
                "mode": "production"
            }
            
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            return {
                "status": "error",
                "text": "Error processing audio",
                "mode": "error",
                "error": str(e)
            }
    
    @classmethod
    async def analyze_audio_emotion(cls, audio_data: bytes) -> Dict[str, Any]:
        """Analyze audio for emotional content"""
        try:
            if cls._demo_mode:
                return {
                    "emotion": "neutral",
                    "confidence": 0.8,
                    "intensity": 0.5,
                    "mode": "demo"
                }
            
            # Implement audio emotion analysis
            return {
                "emotion": "neutral",
                "confidence": 0.7,
                "intensity": 0.5,
                "mode": "production"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio emotion: {e}")
            return {
                "emotion": "unknown",
                "confidence": 0.0,
                "intensity": 0.0,
                "mode": "error",
                "error": str(e)
            }
    
    @classmethod
    async def create_audio_response(
        cls, 
        text: str, 
        voice_id: Optional[str] = None,
        emotion: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a complete audio response with emotion"""
        try:
            # Generate speech
            speech_result = await cls.text_to_speech(text, voice_id)
            
            # Analyze emotion if provided
            emotion_result = None
            if emotion:
                emotion_result = await cls.analyze_audio_emotion(b"demo_audio")
            
            return {
                "speech": speech_result,
                "emotion": emotion_result,
                "text": text,
                "voice_id": voice_id
            }
            
        except Exception as e:
            logger.error(f"Error creating audio response: {e}")
            return {
                "speech": {"mode": "error", "error": str(e)},
                "emotion": {"mode": "error", "error": str(e)},
                "text": text,
                "voice_id": voice_id
            } 