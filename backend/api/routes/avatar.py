from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json
import os
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class AvatarConfig(BaseModel):
    """Avatar configuration model"""
    avatar_id: str
    name: str
    model_path: str
    voice_id: str
    personality: str
    appearance: Dict[str, Any]
    animations: List[str]

class AvatarPreset(BaseModel):
    """Avatar preset model"""
    preset_id: str
    name: str
    description: str
    config: AvatarConfig

# Default avatar presets
DEFAULT_AVATARS = {
    "default": {
        "avatar_id": "default",
        "name": "Default Avatar",
        "model_path": "models/default_avatar.fbx",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "personality": "You are a helpful and friendly virtual assistant. You speak clearly and express emotions naturally through your facial expressions and gestures.",
        "appearance": {
            "skin_tone": "medium",
            "hair_color": "brown",
            "eye_color": "brown",
            "clothing_style": "casual"
        },
        "animations": ["idle", "talking", "gesturing", "listening"]
    },
    "teacher": {
        "avatar_id": "teacher",
        "name": "Virtual Teacher",
        "model_path": "models/teacher_avatar.fbx",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "personality": "You are an experienced and knowledgeable teacher. You explain complex topics clearly, use examples, and encourage learning through interactive conversation.",
        "appearance": {
            "skin_tone": "medium",
            "hair_color": "black",
            "eye_color": "brown",
            "clothing_style": "professional"
        },
        "animations": ["idle", "teaching", "explaining", "encouraging", "thinking"]
    },
    "assistant": {
        "avatar_id": "assistant",
        "name": "AI Assistant",
        "model_path": "models/assistant_avatar.fbx",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "personality": "You are a professional AI assistant. You provide accurate information, help with tasks, and maintain a helpful and efficient demeanor.",
        "appearance": {
            "skin_tone": "medium",
            "hair_color": "blonde",
            "eye_color": "blue",
            "clothing_style": "business"
        },
        "animations": ["idle", "assisting", "thinking", "confirming", "helping"]
    }
}

@router.get("/presets", response_model=List[AvatarPreset])
async def get_avatar_presets():
    """Get available avatar presets"""
    try:
        presets = []
        
        for preset_id, preset_data in DEFAULT_AVATARS.items():
            preset = AvatarPreset(
                preset_id=preset_id,
                name=preset_data["name"],
                description=f"Pre-configured {preset_data['name'].lower()}",
                config=AvatarConfig(**preset_data)
            )
            presets.append(preset)
        
        return presets
        
    except Exception as e:
        logger.error(f"Error getting avatar presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/{preset_id}", response_model=AvatarPreset)
async def get_avatar_preset(preset_id: str):
    """Get a specific avatar preset"""
    try:
        if preset_id not in DEFAULT_AVATARS:
            raise HTTPException(status_code=404, detail="Avatar preset not found")
        
        preset_data = DEFAULT_AVATARS[preset_id]
        preset = AvatarPreset(
            preset_id=preset_id,
            name=preset_data["name"],
            description=f"Pre-configured {preset_data['name'].lower()}",
            config=AvatarConfig(**preset_data)
        )
        
        return preset
        
    except Exception as e:
        logger.error(f"Error getting avatar preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_custom_avatar(config: AvatarConfig):
    """Create a custom avatar configuration"""
    try:
        # Validate the configuration
        if not config.name or not config.model_path:
            raise HTTPException(status_code=400, detail="Name and model path are required")
        
        # In a real implementation, you'd save this to a database
        # For now, we'll just return the created config
        
        return {
            "message": "Avatar created successfully",
            "avatar_id": config.avatar_id,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Error creating avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update/{avatar_id}")
async def update_avatar(avatar_id: str, config: AvatarConfig):
    """Update an existing avatar configuration"""
    try:
        # Validate the configuration
        if not config.name or not config.model_path:
            raise HTTPException(status_code=400, detail="Name and model path are required")
        
        # In a real implementation, you'd update the database
        # For now, we'll just return the updated config
        
        return {
            "message": f"Avatar {avatar_id} updated successfully",
            "avatar_id": avatar_id,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Error updating avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{avatar_id}")
async def delete_avatar(avatar_id: str):
    """Delete an avatar configuration"""
    try:
        # In a real implementation, you'd delete from the database
        # For now, we'll just return a success message
        
        return {
            "message": f"Avatar {avatar_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_available_models():
    """Get available 3D avatar models"""
    try:
        # In a real implementation, you'd scan a models directory
        # For now, we'll return some example models
        
        models = [
            {
                "model_id": "default_avatar",
                "name": "Default Avatar",
                "path": "models/default_avatar.fbx",
                "type": "humanoid",
                "polygon_count": "10k-50k",
                "texture_resolution": "2048x2048"
            },
            {
                "model_id": "teacher_avatar",
                "name": "Teacher Avatar",
                "path": "models/teacher_avatar.fbx",
                "type": "humanoid",
                "polygon_count": "15k-75k",
                "texture_resolution": "4096x4096"
            },
            {
                "model_id": "assistant_avatar",
                "name": "Assistant Avatar",
                "path": "models/assistant_avatar.fbx",
                "type": "humanoid",
                "polygon_count": "12k-60k",
                "texture_resolution": "2048x2048"
            }
        ]
        
        return models
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalities")
async def get_personality_templates():
    """Get personality templates for avatars"""
    try:
        personalities = [
            {
                "id": "friendly",
                "name": "Friendly",
                "description": "Warm, approachable, and easy to talk to",
                "template": "You are a friendly and welcoming person. You smile often, use positive language, and make people feel comfortable in conversation."
            },
            {
                "id": "professional",
                "name": "Professional",
                "description": "Formal, knowledgeable, and business-like",
                "template": "You are a professional and knowledgeable expert. You speak clearly, provide accurate information, and maintain a helpful but formal demeanor."
            },
            {
                "id": "enthusiastic",
                "name": "Enthusiastic",
                "description": "Energetic, passionate, and engaging",
                "template": "You are enthusiastic and passionate about helping others. You use expressive language, show excitement, and engage people with your energy."
            },
            {
                "id": "calm",
                "name": "Calm",
                "description": "Relaxed, patient, and soothing",
                "template": "You are calm and patient. You speak slowly and clearly, provide thoughtful responses, and create a peaceful atmosphere."
            },
            {
                "id": "humorous",
                "name": "Humorous",
                "description": "Funny, witty, and entertaining",
                "template": "You are humorous and entertaining. You use wit and humor appropriately, make people laugh, and keep conversations engaging and fun."
            }
        ]
        
        return personalities
        
    except Exception as e:
        logger.error(f"Error getting personality templates: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 