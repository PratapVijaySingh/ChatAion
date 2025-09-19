"""
Animation Service for Virtual Human API
Handles avatar animation and MediaPipe integration
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
import websockets
from core.config import settings

logger = logging.getLogger(__name__)

class AnimationService:
    """Service for managing avatar animations"""
    
    _is_healthy: bool = False
    _demo_mode: bool = False
    _websocket_connection = None
    _animation_queue: List[Dict[str, Any]] = []
    
    @classmethod
    async def initialize(cls):
        """Initialize the Animation service"""
        try:
            # Check if Unity WebSocket is configured
            if not settings.unity.websocket_url or settings.unity.websocket_url == "ws://localhost:8080":
                logger.warning("Unity WebSocket not configured. Running in demo mode.")
                cls._is_healthy = True
                cls._demo_mode = True
                return
            
            # Try to connect to Unity WebSocket
            try:
                cls._websocket_connection = await websockets.connect(
                    settings.unity.websocket_url,
                    timeout=settings.unity.websocket_timeout
                )
                cls._is_healthy = True
                cls._demo_mode = False
                logger.info("Animation service connected to Unity successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Unity: {e}. Running in demo mode.")
                cls._is_healthy = True
                cls._demo_mode = True
                
        except Exception as e:
            logger.error(f"Failed to initialize Animation service: {e}")
            cls._is_healthy = False
            cls._demo_mode = True
    
    @classmethod
    async def cleanup(cls):
        """Cleanup resources"""
        if cls._websocket_connection:
            await cls._websocket_connection.close()
        cls._is_healthy = False
        logger.info("Animation service cleaned up")
    
    @classmethod
    def is_healthy(cls) -> bool:
        """Check if the service is healthy"""
        return cls._is_healthy
    
    @classmethod
    async def create_complete_animation(
        cls,
        animation_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a complete animation sequence"""
        try:
            if cls._demo_mode:
                return {
                    "animation_id": f"demo_{animation_type}_{len(cls._animation_queue)}",
                    "type": animation_type,
                    "parameters": parameters,
                    "status": "created",
                    "mode": "demo"
                }
            
            # Create animation data
            animation_data = cls._create_animation_data(animation_type, parameters)
            
            # Send to Unity if connected
            if cls._websocket_connection:
                await cls.send_animation_data(animation_data)
            
            return {
                "animation_id": f"anim_{animation_type}_{len(cls._animation_queue)}",
                "type": animation_type,
                "parameters": parameters,
                "status": "created",
                "mode": "production"
            }
            
        except Exception as e:
            logger.error(f"Error creating animation: {e}")
            return {
                "animation_id": "error",
                "type": animation_type,
                "parameters": parameters,
                "status": "error",
                "mode": "error",
                "error": str(e)
            }
    
    @classmethod
    async def create_blendshape_animation(
        cls,
        blendshapes: Dict[str, float],
        duration: float = 1.0
    ) -> Dict[str, Any]:
        """Create facial blendshape animation"""
        try:
            if cls._demo_mode:
                return {
                    "type": "blendshape",
                    "blendshapes": blendshapes,
                    "duration": duration,
                    "status": "created",
                    "mode": "demo"
                }
            
            # Process blendshapes
            processed_blendshapes = cls._process_face_mesh_landmarks(blendshapes)
            
            # Send to Unity
            if cls._websocket_connection:
                await cls.send_animation_data({
                    "type": "blendshape",
                    "data": processed_blendshapes,
                    "duration": duration
                })
            
            return {
                "type": "blendshape",
                "blendshapes": processed_blendshapes,
                "duration": duration,
                "status": "created",
                "mode": "production"
            }
            
        except Exception as e:
            logger.error(f"Error creating blendshape animation: {e}")
            return {
                "type": "blendshape",
                "blendshapes": blendshapes,
                "duration": duration,
                "status": "error",
                "mode": "error",
                "error": str(e)
            }
    
    @classmethod
    async def create_gesture_animation(
        cls,
        gesture_type: str,
        intensity: float = 1.0
    ) -> Dict[str, Any]:
        """Create gesture animation"""
        try:
            if cls._demo_mode:
                return {
                    "type": "gesture",
                    "gesture": gesture_type,
                    "intensity": intensity,
                    "status": "created",
                    "mode": "demo"
                }
            
            # Process gesture
            gesture_data = cls._detect_gestures_from_pose(gesture_type, intensity)
            
            # Send to Unity
            if cls._websocket_connection:
                await cls.send_animation_data({
                    "type": "gesture",
                    "data": gesture_data
                })
            
            return {
                "type": "gesture",
                "gesture": gesture_type,
                "intensity": intensity,
                "status": "created",
                "mode": "production"
            }
            
        except Exception as e:
            logger.error(f"Error creating gesture animation: {e}")
            return {
                "type": "gesture",
                "gesture": gesture_type,
                "intensity": intensity,
                "status": "error",
                "mode": "error",
                "error": str(e)
            }
    
    @classmethod
    async def send_animation_data(cls, animation_data: Dict[str, Any]):
        """Send animation data to Unity via WebSocket"""
        try:
            if cls._websocket_connection and not cls._demo_mode:
                await cls._websocket_connection.send(json.dumps(animation_data))
                logger.debug(f"Sent animation data: {animation_data['type']}")
            else:
                logger.debug(f"Demo mode - animation data: {animation_data['type']}")
        except Exception as e:
            logger.error(f"Error sending animation data: {e}")
    
    @classmethod
    def _create_animation_data(cls, animation_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create animation data structure"""
        return {
            "type": animation_type,
            "parameters": parameters,
            "timestamp": asyncio.get_event_loop().time(),
            "id": f"anim_{len(cls._animation_queue)}"
        }
    
    @classmethod
    def _process_face_mesh_landmarks(cls, landmarks: Dict[str, float]) -> Dict[str, float]:
        """Process MediaPipe face mesh landmarks"""
        processed = {}
        for key, value in landmarks.items():
            # Map MediaPipe landmarks to ARKit blendshapes
            arkit_key = cls._map_blendshapes_to_arkit(key)
            if arkit_key:
                processed[arkit_key] = value
        return processed
    
    @classmethod
    def _map_blendshapes_to_arkit(cls, mediapipe_key: str) -> Optional[str]:
        """Map MediaPipe landmarks to ARKit blendshapes"""
        mapping = {
            "browDown_L": "browDown_L",
            "browDown_R": "browDown_R",
            "browUp_L": "browUp_L",
            "browUp_R": "browUp_R",
            "cheekPuff": "cheekPuff",
            "eyeBlink_L": "eyeBlink_L",
            "eyeBlink_R": "eyeBlink_R",
            "eyeLookDown_L": "eyeLookDown_L",
            "eyeLookDown_R": "eyeLookDown_R",
            "eyeLookIn_L": "eyeLookIn_L",
            "eyeLookIn_R": "eyeLookIn_R",
            "eyeLookOut_L": "eyeLookOut_L",
            "eyeLookOut_R": "eyeLookOut_R",
            "eyeLookUp_L": "eyeLookUp_L",
            "eyeLookUp_R": "eyeLookUp_R",
            "jawForward": "jawForward",
            "jawLeft": "jawLeft",
            "jawOpen": "jawOpen",
            "jawRight": "jawRight",
            "mouthClose": "mouthClose",
            "mouthFunnel": "mouthFunnel",
            "mouthLeft": "mouthLeft",
            "mouthPucker": "mouthPucker",
            "mouthRight": "mouthRight",
            "mouthSmile_L": "mouthSmile_L",
            "mouthSmile_R": "mouthSmile_R",
            "mouthFrown_L": "mouthFrown_L",
            "mouthFrown_R": "mouthFrown_R"
        }
        return mapping.get(mediapipe_key)
    
    @classmethod
    def _detect_gestures_from_pose(cls, gesture_type: str, intensity: float) -> Dict[str, Any]:
        """Detect gestures from pose data"""
        gestures = {
            "wave": {"hand": "right", "motion": "side_to_side", "intensity": intensity},
            "point": {"hand": "right", "motion": "forward", "intensity": intensity},
            "thumbs_up": {"hand": "right", "motion": "upward", "intensity": intensity},
            "shake_head": {"head": "side_to_side", "intensity": intensity},
            "nod": {"head": "up_down", "intensity": intensity}
        }
        return gestures.get(gesture_type, {"type": "unknown", "intensity": intensity})
    
    @classmethod
    def _get_blendshape_category(cls, blendshape_name: str) -> str:
        """Get the category of a blendshape"""
        categories = {
            "brow": ["browDown", "browUp"],
            "eye": ["eyeBlink", "eyeLook"],
            "mouth": ["mouthClose", "mouthOpen", "mouthSmile", "mouthFrown"],
            "jaw": ["jawOpen", "jawForward", "jawLeft", "jawRight"],
            "cheek": ["cheekPuff"]
        }
        
        for category, names in categories.items():
            if any(name in blendshape_name for name in names):
                return category
        return "other"
    
    @classmethod
    async def trigger_gesture(cls, gesture_type: str, parameters: Dict[str, Any] = None):
        """Trigger a specific gesture"""
        try:
            if parameters is None:
                parameters = {}
            
            gesture_data = await cls.create_gesture_animation(gesture_type, parameters.get("intensity", 1.0))
            
            # Add to animation queue
            cls._animation_queue.append(gesture_data)
            
            return gesture_data
            
        except Exception as e:
            logger.error(f"Error triggering gesture: {e}")
            return {
                "type": "gesture",
                "gesture": gesture_type,
                "status": "error",
                "error": str(e)
            }
    
    @classmethod
    def get_animation_status(cls) -> Dict[str, Any]:
        """Get current animation status"""
        return {
            "queue_length": len(cls._animation_queue),
            "websocket_connected": cls._websocket_connection is not None,
            "demo_mode": cls._demo_mode,
            "healthy": cls._is_healthy
        } 