"""
Configuration settings for Virtual Human API
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class OpenAISettings(BaseSettings):
    """OpenAI configuration"""
    api_key: str = Field(default="your_openai_api_key_here", env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

class ElevenLabsSettings(BaseSettings):
    """ElevenLabs configuration"""
    api_key: str = Field(default="your_elevenlabs_api_key_here", env="ELEVENLABS_API_KEY")
    voice_id: str = Field(default="your_voice_id_here", env="ELEVENLABS_VOICE_ID")

class AudioSettings(BaseSettings):
    """Audio configuration"""
    sample_rate: int = Field(default=22050, env="AUDIO_SAMPLE_RATE")
    channels: int = Field(default=1, env="AUDIO_CHANNELS")
    format: str = Field(default="wav", env="AUDIO_FORMAT")

class AnimationSettings(BaseSettings):
    """Animation configuration"""
    fps: int = Field(default=30, env="ANIMATION_FPS")
    smoothing: float = Field(default=0.1, env="ANIMATION_SMOOTHING")

class MediaPipeSettings(BaseSettings):
    """MediaPipe configuration"""
    face_mesh: bool = Field(default=True, env="MEDIAPIPE_FACE_MESH")
    hand_tracking: bool = Field(default=True, env="MEDIAPIPE_HAND_TRACKING")
    pose_tracking: bool = Field(default=True, env="MEDIAPIPE_POSE_TRACKING")

class UnitySettings(BaseSettings):
    """Unity communication configuration"""
    websocket_url: str = Field(default="ws://localhost:8080", env="UNITY_WEBSOCKET_URL")
    websocket_timeout: int = Field(default=30, env="UNITY_WEBSOCKET_TIMEOUT")

class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    db: int = Field(default=0, env="REDIS_DB")

class CelerySettings(BaseSettings):
    """Celery configuration"""
    broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

class ServerSettings(BaseSettings):
    """Server configuration"""
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")

class Settings(BaseSettings):
    """Main settings class"""
    openai: OpenAISettings = OpenAISettings()
    elevenlabs: ElevenLabsSettings = ElevenLabsSettings()
    audio: AudioSettings = AudioSettings()
    animation: AnimationSettings = AnimationSettings()
    mediapipe: MediaPipeSettings = MediaPipeSettings()
    unity: UnitySettings = UnitySettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    server: ServerSettings = ServerSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create global settings instance
settings = Settings() 