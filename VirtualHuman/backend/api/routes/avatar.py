"""
Avatar API routes for Virtual Human
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Default avatar presets
DEFAULT_AVATARS = {
    "teacher": {
        "id": "teacher",
        "name": "Professional Teacher",
        "description": "A professional educator avatar",
        "personality": "helpful, knowledgeable, patient",
        "voice_id": "default_voice_1",
        "appearance": {
            "gender": "neutral",
            "age": "adult",
            "style": "professional"
        }
    },
    "tutor": {
        "id": "tutor",
        "name": "Friendly Tutor",
        "description": "A friendly and approachable tutor",
        "personality": "friendly, encouraging, supportive",
        "voice_id": "default_voice_2",
        "appearance": {
            "gender": "neutral",
            "age": "young_adult",
            "style": "casual"
        }
    },
    "expert": {
        "id": "expert",
        "name": "Subject Expert",
        "description": "A specialized subject matter expert",
        "personality": "authoritative, precise, thorough",
        "voice_id": "default_voice_3",
        "appearance": {
            "gender": "neutral",
            "age": "adult",
            "style": "academic"
        }
    }
}

# In-memory storage for custom avatars
custom_avatars = {}

@router.get("/presets")
async def get_avatar_presets():
    """Get available avatar presets"""
    try:
        return {
            "presets": list(DEFAULT_AVATARS.values()),
            "total": len(DEFAULT_AVATARS)
        }
        
    except Exception as e:
        logger.error(f"Error getting avatar presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/{preset_id}")
async def get_avatar_preset(preset_id: str):
    """Get a specific avatar preset"""
    try:
        if preset_id not in DEFAULT_AVATARS:
            raise HTTPException(status_code=404, detail="Avatar preset not found")
        
        return DEFAULT_AVATARS[preset_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting avatar preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_custom_avatar(avatar_data: Dict[str, Any]):
    """Create a custom avatar"""
    try:
        avatar_id = avatar_data.get("id")
        name = avatar_data.get("name")
        
        if not avatar_id or not name:
            raise HTTPException(status_code=400, detail="Avatar ID and name are required")
        
        if avatar_id in custom_avatars:
            raise HTTPException(status_code=400, detail="Avatar ID already exists")
        
        # Create custom avatar
        custom_avatar = {
            "id": avatar_id,
            "name": name,
            "description": avatar_data.get("description", ""),
            "personality": avatar_data.get("personality", ""),
            "voice_id": avatar_data.get("voice_id", "default_voice_1"),
            "appearance": avatar_data.get("appearance", {}),
            "custom": True
        }
        
        custom_avatars[avatar_id] = custom_avatar
        
        return {
            "message": "Custom avatar created successfully",
            "avatar": custom_avatar
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update/{avatar_id}")
async def update_avatar(avatar_id: str, avatar_data: Dict[str, Any]):
    """Update an existing avatar"""
    try:
        # Check if avatar exists
        if avatar_id in DEFAULT_AVATARS:
            raise HTTPException(status_code=400, detail="Cannot modify default avatars")
        
        if avatar_id not in custom_avatars:
            raise HTTPException(status_code=404, detail="Custom avatar not found")
        
        # Update avatar
        custom_avatars[avatar_id].update(avatar_data)
        
        return {
            "message": "Avatar updated successfully",
            "avatar": custom_avatars[avatar_id]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{avatar_id}")
async def delete_avatar(avatar_id: str):
    """Delete a custom avatar"""
    try:
        if avatar_id in DEFAULT_AVATARS:
            raise HTTPException(status_code=400, detail="Cannot delete default avatars")
        
        if avatar_id not in custom_avatars:
            raise HTTPException(status_code=404, detail="Custom avatar not found")
        
        # Delete avatar
        deleted_avatar = custom_avatars.pop(avatar_id)
        
        return {
            "message": "Avatar deleted successfully",
            "deleted_avatar": deleted_avatar
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_avatar_models():
    """Get available avatar models"""
    try:
        models = [
            {
                "id": "realistic",
                "name": "Realistic Human",
                "description": "Photorealistic human avatar",
                "complexity": "high"
            },
            {
                "id": "stylized",
                "name": "Stylized Character",
                "description": "Artistic, stylized character",
                "complexity": "medium"
            },
            {
                "id": "cartoon",
                "name": "Cartoon Style",
                "description": "Fun, cartoon-style avatar",
                "complexity": "low"
            }
        ]
        
        return {"models": models}
        
    except Exception as e:
        logger.error(f"Error getting avatar models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalities")
async def get_personality_templates():
    """Get personality templates"""
    try:
        personalities = [
            {
                "id": "teacher",
                "name": "Teacher",
                "traits": ["patient", "knowledgeable", "encouraging"],
                "style": "educational"
            },
            {
                "id": "mentor",
                "name": "Mentor",
                "traits": ["wise", "supportive", "challenging"],
                "style": "developmental"
            },
            {
                "id": "friend",
                "name": "Friend",
                "traits": ["friendly", "casual", "supportive"],
                "style": "conversational"
            },
            {
                "id": "expert",
                "name": "Expert",
                "traits": ["authoritative", "precise", "thorough"],
                "style": "professional"
            }
        ]
        
        return {"personalities": personalities}
        
    except Exception as e:
        logger.error(f"Error getting personality templates: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 