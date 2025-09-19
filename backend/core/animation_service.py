import asyncio
import logging
import json
import websockets
from typing import Dict, List, Optional, Any, Tuple
import mediapipe as mp
import cv2
import numpy as np
from core.config import settings

logger = logging.getLogger(__name__)

class AnimationService:
    """Service for managing avatar animation and Unity communication"""
    
    _initialized: bool = False
    _unity_websocket: Optional[websockets.WebSocketServerProtocol] = None
    _mediapipe_face_mesh: Optional[mp.solutions.face_mesh.FaceMesh] = None
    _mediapipe_hands: Optional[mp.solutions.hands.Hands] = None
    _mediapipe_pose: Optional[mp.solutions.pose.Pose] = None
    
    # Standard ARKit blendshapes
    ARKIT_BLENDSHAPES = [
        "browDown_L", "browDown_R", "browInnerUp", "browOuterUp_L", "browOuterUp_R",
        "cheekPuff", "cheekSquint_L", "cheekSquint_R", "eyeBlink_L", "eyeBlink_R",
        "eyeLookDown_L", "eyeLookDown_R", "eyeLookIn_L", "eyeLookIn_R", "eyeLookOut_L",
        "eyeLookOut_R", "eyeLookUp_L", "eyeLookUp_R", "eyeSquint_L", "eyeSquint_R",
        "eyeWide_L", "eyeWide_R", "jawForward", "jawLeft", "jawOpen", "jawRight",
        "mouthClose", "mouthDimple_L", "mouthDimple_R", "mouthFrown_L", "mouthFrown_R",
        "mouthFunnel", "mouthLeft", "mouthLowerDown_L", "mouthLowerDown_R", "mouthPress_L",
        "mouthPress_R", "mouthPucker", "mouthRight", "mouthRollLower", "mouthRollUpper",
        "mouthShrugLower", "mouthShrugUpper", "mouthSmile_L", "mouthSmile_R", "mouthStretch_L",
        "mouthStretch_R", "mouthUpperUp_L", "mouthUpperUp_R", "noseSneer_L", "noseSneer_R",
        "tongueOut", "tongueUp", "tongueDown", "tongueLeft", "tongueRight"
    ]
    
    @classmethod
    async def initialize(cls):
        """Initialize the animation service"""
        try:
            # Initialize MediaPipe components
            if settings.mediapipe_face_mesh:
                cls._mediapipe_face_mesh = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            
            if settings.mediapipe_hands:
                cls._mediapipe_hands = mp.solutions.hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.5
                )
            
            if settings.mediapipe_pose:
                cls._mediapipe_pose = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            
            cls._initialized = True
            logger.info("Animation service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize animation service: {e}")
            raise
    
    @classmethod
    async def cleanup(cls):
        """Cleanup the animation service"""
        try:
            if cls._unity_websocket:
                await cls._unity_websocket.close()
                cls._unity_websocket = None
            
            if cls._mediapipe_face_mesh:
                cls._mediapipe_face_mesh.close()
                cls._mediapipe_face_mesh = None
            
            if cls._mediapipe_hands:
                cls._mediapipe_hands.close()
                cls._mediapipe_hands = None
            
            if cls._mediapipe_pose:
                cls._mediapipe_pose.close()
                cls._mediapipe_pose = None
            
            cls._initialized = False
            logger.info("Animation service cleaned up")
            
        except Exception as e:
            logger.error(f"Error during animation service cleanup: {e}")
    
    @classmethod
    async def is_healthy(cls) -> bool:
        """Check if the animation service is healthy"""
        return cls._initialized
    
    @classmethod
    async def connect_to_unity(cls) -> bool:
        """Connect to Unity via WebSocket"""
        try:
            cls._unity_websocket = await websockets.connect(settings.unity_websocket_url)
            logger.info("Connected to Unity WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Unity: {e}")
            return False
    
    @classmethod
    async def send_animation_data(cls, animation_data: Dict[str, Any]) -> bool:
        """Send animation data to Unity"""
        if not cls._unity_websocket:
            if not await cls.connect_to_unity():
                return False
        
        try:
            message = json.dumps(animation_data)
            await cls._unity_websocket.send(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send animation data to Unity: {e}")
            # Try to reconnect
            cls._unity_websocket = None
            return False
    
    @classmethod
    async def process_facial_animation(
        cls,
        image: np.ndarray,
        emotion: str = "neutral"
    ) -> Dict[str, float]:
        """Process facial animation using MediaPipe and return blendshape weights"""
        if not cls._initialized or not cls._mediapipe_face_mesh:
            return cls._get_default_blendshapes(emotion)
        
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = cls._mediapipe_face_mesh.process(rgb_image)
            
            if not results.multi_face_landmarks:
                return cls._get_default_blendshapes(emotion)
            
            # Get face landmarks
            face_landmarks = results.multi_face_landmarks[0]
            
            # Calculate blendshape weights based on landmarks
            blendshapes = cls._calculate_blendshapes_from_landmarks(face_landmarks)
            
            # Apply emotion overlay
            emotion_blendshapes = cls._apply_emotion_overlay(blendshapes, emotion)
            
            return emotion_blendshapes
            
        except Exception as e:
            logger.error(f"Facial animation processing failed: {e}")
            return cls._get_default_blendshapes(emotion)
    
    @classmethod
    def _calculate_blendshapes_from_landmarks(
        cls,
        landmarks
    ) -> Dict[str, float]:
        """Calculate blendshape weights from MediaPipe landmarks"""
        blendshapes = {}
        
        # Extract key landmark points
        points = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        # Calculate basic facial expressions
        # Eye blink detection
        left_eye_height = cls._calculate_eye_height(points, "left")
        right_eye_height = cls._calculate_eye_height(points, "right")
        
        blendshapes["eyeBlink_L"] = max(0, 1 - left_eye_height / 0.1)
        blendshapes["eyeBlink_R"] = max(0, 1 - right_eye_height / 0.1)
        
        # Mouth open detection
        mouth_height = cls._calculate_mouth_height(points)
        blendshapes["jawOpen"] = min(1, mouth_height / 0.15)
        
        # Smile detection
        smile_intensity = cls._calculate_smile_intensity(points)
        blendshapes["mouthSmile_L"] = smile_intensity
        blendshapes["mouthSmile_R"] = smile_intensity
        
        # Initialize other blendshapes to 0
        for blendshape in cls.ARKIT_BLENDSHAPES:
            if blendshape not in blendshapes:
                blendshapes[blendshape] = 0.0
        
        return blendshapes
    
    @classmethod
    def _calculate_eye_height(cls, points: np.ndarray, eye: str) -> float:
        """Calculate eye height for blink detection"""
        if eye == "left":
            # Left eye landmarks (approximate indices)
            eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        else:
            # Right eye landmarks
            eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        if len(points) > max(eye_indices):
            eye_points = points[eye_indices]
            height = np.max(eye_points[:, 1]) - np.min(eye_points[:, 1])
            return height
        return 0.1
    
    @classmethod
    def _calculate_mouth_height(cls, points: np.ndarray) -> float:
        """Calculate mouth height for jaw open detection"""
        # Mouth landmarks (approximate indices)
        mouth_indices = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        
        if len(points) > max(mouth_indices):
            mouth_points = points[mouth_indices]
            height = np.max(mouth_points[:, 1]) - np.min(mouth_points[:, 1])
            return height
        return 0.0
    
    @classmethod
    def _calculate_smile_intensity(cls, points: np.ndarray) -> float:
        """Calculate smile intensity from mouth corners"""
        # Mouth corner landmarks (approximate indices)
        left_corner = 61
        right_corner = 291
        
        if len(points) > max(left_corner, right_corner):
            left_point = points[left_corner]
            right_point = points[right_corner]
            
            # Calculate distance between corners
            distance = np.linalg.norm(left_point - right_point)
            
            # Normalize to 0-1 range (approximate)
            normalized_distance = min(1, distance / 0.3)
            return normalized_distance
        
        return 0.0
    
    @classmethod
    def _apply_emotion_overlay(
        cls,
        blendshapes: Dict[str, float],
        emotion: str
    ) -> Dict[str, float]:
        """Apply emotion-specific blendshape modifications"""
        emotion_modifiers = {
            "happy": {
                "mouthSmile_L": 0.8,
                "mouthSmile_R": 0.8,
                "cheekSquint_L": 0.6,
                "cheekSquint_R": 0.6,
                "eyeWide_L": 0.3,
                "eyeWide_R": 0.3
            },
            "sad": {
                "mouthFrown_L": 0.7,
                "mouthFrown_R": 0.7,
                "browDown_L": 0.6,
                "browDown_R": 0.6,
                "eyeSquint_L": 0.4,
                "eyeSquint_R": 0.4
            },
            "excited": {
                "mouthSmile_L": 0.9,
                "mouthSmile_R": 0.9,
                "eyeWide_L": 0.8,
                "eyeWide_R": 0.8,
                "browInnerUp": 0.7,
                "jawOpen": 0.3
            },
            "angry": {
                "browDown_L": 0.8,
                "browDown_R": 0.8,
                "mouthFrown_L": 0.6,
                "mouthFrown_R": 0.6,
                "eyeSquint_L": 0.7,
                "eyeSquint_R": 0.7
            }
        }
        
        if emotion in emotion_modifiers:
            for blendshape, value in emotion_modifiers[emotion].items():
                if blendshape in blendshapes:
                    blendshapes[blendshape] = max(blendshapes[blendshape], value)
        
        return blendshapes
    
    @classmethod
    def _get_default_blendshapes(cls, emotion: str) -> Dict[str, float]:
        """Get default blendshape values for an emotion"""
        blendshapes = {blendshape: 0.0 for blendshape in cls.ARKIT_BLENDSHAPES}
        
        # Apply basic emotion defaults
        if emotion == "happy":
            blendshapes["mouthSmile_L"] = 0.5
            blendshapes["mouthSmile_R"] = 0.5
        elif emotion == "sad":
            blendshapes["mouthFrown_L"] = 0.5
            blendshapes["mouthFrown_R"] = 0.5
        elif emotion == "excited":
            blendshapes["eyeWide_L"] = 0.3
            blendshapes["eyeWide_R"] = 0.3
        
        return blendshapes
    
    @classmethod
    async def create_gesture_animation(
        cls,
        gesture_type: str,
        intensity: float = 1.0
    ) -> Dict[str, Any]:
        """Create gesture animation data"""
        gesture_animations = {
            "nod": {
                "head_rotation_y": [0, 15, 0, -15, 0],
                "duration": 1.0
            },
            "shake_head": {
                "head_rotation_y": [0, -15, 0, 15, 0],
                "duration": 1.0
            },
            "wave": {
                "hand_rotation_z": [0, 45, -45, 45, 0],
                "duration": 1.5
            },
            "point": {
                "finger_extension": [0, 1, 1, 0],
                "duration": 0.8
            }
        }
        
        if gesture_type in gesture_animations:
            animation = gesture_animations[gesture_type].copy()
            animation["intensity"] = intensity
            animation["gesture_type"] = gesture_type
            return animation
        
        return {"gesture_type": "unknown", "intensity": intensity}
    
    @classmethod
    async def create_complete_animation(
        cls,
        blendshapes: Dict[str, float],
        gestures: List[str] = None,
        emotion: str = "neutral"
    ) -> Dict[str, Any]:
        """Create complete animation data for Unity"""
        animation_data = {
            "type": "animation_update",
            "timestamp": asyncio.get_event_loop().time(),
            "blendshapes": blendshapes,
            "emotion": emotion,
            "gestures": gestures or [],
            "fps": settings.animation_fps
        }
        
        return animation_data 