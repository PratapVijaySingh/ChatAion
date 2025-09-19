from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    api_title: str = "Virtual Human API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.7
    
    # ElevenLabs Configuration
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
    
    # Audio Configuration
    audio_sample_rate: int = 44100
    audio_channels: int = 1
    audio_format: str = "wav"
    max_audio_duration: int = 30  # seconds
    
    # Animation Configuration
    animation_fps: int = 30
    blendshape_count: int = 52  # Standard ARKit blendshapes
    gesture_trigger_threshold: float = 0.8
    
    # MediaPipe Configuration
    mediapipe_face_mesh: bool = True
    mediapipe_hands: bool = True
    mediapipe_pose: bool = False
    
    # Unity Communication
    unity_websocket_url: str = "ws://localhost:8080"
    unity_timeout: int = 30
    
    # Redis Configuration (for caching and queuing)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # Celery Configuration (for background tasks)
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Load from environment variables
def load_settings():
    """Load settings from environment variables"""
    settings.openai_api_key = os.getenv("OPENAI_API_KEY")
    settings.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    settings.debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Override with environment variables if present
    if os.getenv("OPENAI_MODEL"):
        settings.openai_model = os.getenv("OPENAI_MODEL")
    if os.getenv("ELEVENLABS_VOICE_ID"):
        settings.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    if os.getenv("UNITY_WEBSOCKET_URL"):
        settings.unity_websocket_url = os.getenv("UNITY_WEBSOCKET_URL")

# Load settings on import
load_settings() 