"""
Animation API routes for Virtual Human
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import json
import logging

from core.animation_service import AnimationService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/update")
async def update_animation(animation_data: Dict[str, Any]):
    """Update avatar animation"""
    try:
        animation_type = animation_data.get("type", "")
        parameters = animation_data.get("parameters", {})
        
        if not animation_type:
            raise HTTPException(status_code=400, detail="Animation type is required")
        
        # Create animation
        result = await AnimationService.create_complete_animation(animation_type, parameters)
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating animation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/blendshapes")
async def update_blendshapes(blendshape_data: Dict[str, Any]):
    """Update facial blendshapes"""
    try:
        blendshapes = blendshape_data.get("blendshapes", {})
        duration = blendshape_data.get("duration", 1.0)
        
        if not blendshapes:
            raise HTTPException(status_code=400, detail="Blendshapes are required")
        
        # Create blendshape animation
        result = await AnimationService.create_blendshape_animation(blendshapes, duration)
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating blendshapes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gesture")
async def trigger_gesture(gesture_data: Dict[str, Any]):
    """Trigger a specific gesture"""
    try:
        gesture_type = gesture_data.get("gesture", "")
        intensity = gesture_data.get("intensity", 1.0)
        
        if not gesture_type:
            raise HTTPException(status_code=400, detail="Gesture type is required")
        
        # Trigger gesture
        result = await AnimationService.trigger_gesture(gesture_type, gesture_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error triggering gesture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_animation_status():
    """Get current animation status"""
    try:
        status = AnimationService.get_animation_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting animation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def animation_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time animation updates"""
    await websocket.accept()
    
    try:
        while True:
            # Receive animation data from client
            data = await websocket.receive_text()
            animation_data = json.loads(data)
            
            # Process animation
            result = await AnimationService.create_complete_animation(
                animation_data.get("type", "unknown"),
                animation_data.get("parameters", {})
            )
            
            # Send result back
            await websocket.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        logger.info("Animation WebSocket disconnected")
    except Exception as e:
        logger.error(f"Animation WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "error": str(e)
            }))
        except:
            pass 