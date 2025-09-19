from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
from core.animation_service import AnimationService

logger = logging.getLogger(__name__)
router = APIRouter()

class AnimationRequest(BaseModel):
    """Animation request model"""
    blendshapes: Dict[str, float]
    gestures: List[str] = []
    emotion: str = "neutral"
    duration: float = 1.0

class BlendshapeInfo(BaseModel):
    """Blendshape information model"""
    name: str
    value: float
    category: str

@router.post("/update")
async def update_animation(request: AnimationRequest):
    """Update avatar animation"""
    try:
        # Create animation data
        animation_data = await AnimationService.create_complete_animation(
            blendshapes=request.blendshapes,
            gestures=request.gestures,
            emotion=request.emotion
        )
        
        # Send to Unity
        success = await AnimationService.send_animation_data(animation_data)
        
        if not success:
            raise HTTPException(status_code=503, detail="Unity not connected")
        
        return {
            "message": "Animation updated successfully",
            "animation_data": animation_data
        }
        
    except Exception as e:
        logger.error(f"Animation update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blendshapes")
async def get_available_blendshapes():
    """Get available blendshapes"""
    try:
        blendshapes = []
        
        for blendshape in AnimationService.ARKIT_BLENDSHAPES:
            # Categorize blendshapes
            category = "other"
            if "eye" in blendshape.lower():
                category = "eyes"
            elif "mouth" in blendshape.lower():
                category = "mouth"
            elif "brow" in blendshape.lower():
                category = "brows"
            elif "cheek" in blendshape.lower():
                category = "cheeks"
            elif "jaw" in blendshape.lower():
                category = "jaw"
            elif "nose" in blendshape.lower():
                category = "nose"
            elif "tongue" in blendshape.lower():
                category = "tongue"
            
            blendshapes.append(BlendshapeInfo(
                name=blendshape,
                value=0.0,
                category=category
            ))
        
        return blendshapes
        
    except Exception as e:
        logger.error(f"Error getting blendshapes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gesture")
async def trigger_gesture(gesture_type: str, intensity: float = 1.0):
    """Trigger a specific gesture"""
    try:
        # Create gesture animation
        gesture_data = await AnimationService.create_gesture_animation(
            gesture_type=gesture_type,
            intensity=intensity
        )
        
        # Send to Unity
        success = await AnimationService.send_animation_data(gesture_data)
        
        if not success:
            raise HTTPException(status_code=503, detail="Unity not connected")
        
        return {
            "message": f"Gesture {gesture_type} triggered successfully",
            "gesture_data": gesture_data
        }
        
    except Exception as e:
        logger.error(f"Gesture trigger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_animation_status():
    """Get animation service status"""
    try:
        status = {
            "initialized": AnimationService._initialized,
            "unity_connected": AnimationService._unity_websocket is not None,
            "mediapipe_face_mesh": AnimationService._mediapipe_face_mesh is not None,
            "mediapipe_hands": AnimationService._mediapipe_hands is not None,
            "mediapipe_pose": AnimationService._mediapipe_pose is not None
        }
        
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
            
            try:
                # Process animation request
                if animation_data["type"] == "animation_update":
                    # Create complete animation
                    complete_animation = await AnimationService.create_complete_animation(
                        blendshapes=animation_data.get("blendshapes", {}),
                        gestures=animation_data.get("gestures", []),
                        emotion=animation_data.get("emotion", "neutral")
                    )
                    
                    # Send to Unity
                    success = await AnimationService.send_animation_data(complete_animation)
                    
                    # Send confirmation back to client
                    response = {
                        "type": "animation_confirmation",
                        "success": success,
                        "timestamp": animation_data.get("timestamp", 0)
                    }
                    
                    await websocket.send_text(json.dumps(response))
                    
                elif animation_data["type"] == "gesture_trigger":
                    # Trigger gesture
                    gesture_data = await AnimationService.create_gesture_animation(
                        gesture_type=animation_data.get("gesture_type", "wave"),
                        intensity=animation_data.get("intensity", 1.0)
                    )
                    
                    # Send to Unity
                    success = await AnimationService.send_animation_data(gesture_data)
                    
                    # Send confirmation back to client
                    response = {
                        "type": "gesture_confirmation",
                        "success": success,
                        "gesture_type": animation_data.get("gesture_type"),
                        "timestamp": animation_data.get("timestamp", 0)
                    }
                    
                    await websocket.send_text(json.dumps(response))
                    
                else:
                    # Unknown message type
                    response = {
                        "type": "error",
                        "error": f"Unknown message type: {animation_data.get('type')}"
                    }
                    await websocket.send_text(json.dumps(response))
                    
            except Exception as e:
                error_response = {
                    "type": "error",
                    "error": str(e)
                }
                await websocket.send_text(json.dumps(error_response))
                
    except WebSocketDisconnect:
        logger.info("Animation WebSocket disconnected")
    except Exception as e:
        logger.error(f"Animation WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass 