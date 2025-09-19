import asyncio
import logging
import tempfile
import os
from typing import Optional, Dict, Any, BinaryIO
import openai
from elevenlabs import generate, save, set_api_key
from elevenlabs.api import History
import soundfile as sf
import numpy as np
from core.config import settings

logger = logging.getLogger(__name__)

class AudioService:
    """Service for managing audio processing (STT and TTS)"""
    
    _initialized: bool = False
    _elevenlabs_voices: Dict[str, Any] = {}
    
    @classmethod
    async def initialize(cls):
        """Initialize the audio service"""
        try:
            # Initialize OpenAI for Whisper
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            openai.api_key = settings.openai_api_key
            
            # Initialize ElevenLabs
            if not settings.elevenlabs_api_key:
                raise ValueError("ElevenLabs API key not configured")
            set_api_key(settings.elevenlabs_api_key)
            
            # Load available voices
            await cls._load_voices()
            
            cls._initialized = True
            logger.info("Audio service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio service: {e}")
            raise
    
    @classmethod
    async def cleanup(cls):
        """Cleanup the audio service"""
        cls._initialized = False
        cls._elevenlabs_voices.clear()
        logger.info("Audio service cleaned up")
    
    @classmethod
    async def is_healthy(cls) -> bool:
        """Check if the audio service is healthy"""
        return cls._initialized
    
    @classmethod
    async def _load_voices(cls):
        """Load available ElevenLabs voices"""
        try:
            # Get available voices
            voices = await asyncio.to_thread(lambda: History.from_api().voices)
            for voice in voices:
                cls._elevenlabs_voices[voice.voice_id] = {
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description,
                    "labels": voice.labels
                }
            logger.info(f"Loaded {len(cls._elevenlabs_voices)} ElevenLabs voices")
        except Exception as e:
            logger.warning(f"Could not load ElevenLabs voices: {e}")
    
    @classmethod
    async def speech_to_text(
        cls,
        audio_data: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert speech to text using OpenAI Whisper"""
        if not cls._initialized:
            raise RuntimeError("Audio service not initialized")
        
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe audio using Whisper
                with open(temp_file_path, "rb") as audio_file:
                    transcript = await asyncio.to_thread(
                        openai.Audio.transcribe,
                        "whisper-1",
                        audio_file,
                        language=language,
                        prompt=prompt
                    )
                
                return {
                    "text": transcript.text,
                    "language": transcript.language,
                    "confidence": getattr(transcript, 'confidence', None),
                    "duration": getattr(transcript, 'duration', None)
                }
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Speech-to-text conversion failed: {e}")
            raise
    
    @classmethod
    async def text_to_speech(
        cls,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "eleven_monolingual_v1",
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> bytes:
        """Convert text to speech using ElevenLabs"""
        if not cls._initialized:
            raise RuntimeError("Audio service not initialized")
        
        try:
            # Use default voice if none specified
            if not voice_id:
                voice_id = settings.elevenlabs_voice_id
            
            # Generate audio
            audio = await asyncio.to_thread(
                generate,
                text=text,
                voice=voice_id,
                model=model,
                stability=stability,
                similarity_boost=similarity_boost
            )
            
            return audio
            
        except Exception as e:
            logger.error(f"Text-to-speech conversion failed: {e}")
            raise
    
    @classmethod
    async def get_available_voices(cls) -> Dict[str, Any]:
        """Get available ElevenLabs voices"""
        if not cls._initialized:
            raise RuntimeError("Audio service not initialized")
        
        return cls._elevenlabs_voices.copy()
    
    @classmethod
    async def process_audio_stream(
        cls,
        audio_stream: BinaryIO,
        chunk_size: int = 1024
    ) -> bytes:
        """Process audio stream and return complete audio data"""
        audio_chunks = []
        
        while True:
            chunk = audio_stream.read(chunk_size)
            if not chunk:
                break
            audio_chunks.append(chunk)
        
        return b''.join(audio_chunks)
    
    @classmethod
    async def analyze_audio_emotion(
        cls,
        audio_data: bytes
    ) -> Dict[str, Any]:
        """Analyze audio to detect emotional content"""
        try:
            # Convert audio data to numpy array
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Load audio using soundfile
                data, sample_rate = await asyncio.to_thread(sf.read, temp_file_path)
                
                # Basic audio analysis
                duration = len(data) / sample_rate
                amplitude = np.abs(data)
                energy = np.mean(amplitude ** 2)
                
                # Simple emotion detection based on audio characteristics
                emotion_data = {
                    "duration": duration,
                    "energy": float(energy),
                    "sample_rate": sample_rate,
                    "channels": len(data.shape),
                    "detected_emotion": "neutral"
                }
                
                # Emotion classification based on energy and duration
                if energy > 0.1:
                    if duration > 5:
                        emotion_data["detected_emotion"] = "excited"
                    else:
                        emotion_data["detected_emotion"] = "happy"
                elif energy < 0.01:
                    emotion_data["detected_emotion"] = "calm"
                
                return emotion_data
                
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Audio emotion analysis failed: {e}")
            return {
                "detected_emotion": "unknown",
                "error": str(e)
            }
    
    @classmethod
    async def create_audio_response(
        cls,
        text: str,
        voice_id: Optional[str] = None,
        emotion: str = "neutral"
    ) -> Dict[str, Any]:
        """Create audio response with emotion-appropriate voice settings"""
        # Adjust voice parameters based on emotion
        stability = 0.5
        similarity_boost = 0.75
        
        if emotion == "excited":
            stability = 0.3
            similarity_boost = 0.9
        elif emotion == "calm":
            stability = 0.8
            similarity_boost = 0.6
        elif emotion == "sad":
            stability = 0.7
            similarity_boost = 0.8
        
        # Generate audio
        audio_data = await cls.text_to_speech(
            text=text,
            voice_id=voice_id,
            stability=stability,
            similarity_boost=similarity_boost
        )
        
        return {
            "audio_data": audio_data,
            "emotion": emotion,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        } 