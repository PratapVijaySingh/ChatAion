import asyncio
import logging
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for managing LLM interactions"""
    
    _client: Optional[AsyncOpenAI] = None
    _conversation_history: Dict[str, List[Dict[str, Any]]] = {}
    
    @classmethod
    async def initialize(cls):
        """Initialize the LLM service"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        cls._client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("LLM service initialized successfully")
    
    @classmethod
    async def cleanup(cls):
        """Cleanup the LLM service"""
        if cls._client:
            await cls._client.close()
        cls._client = None
        logger.info("LLM service cleaned up")
    
    @classmethod
    async def is_healthy(cls) -> bool:
        """Check if the LLM service is healthy"""
        try:
            if not cls._client:
                return False
            # Test with a simple completion
            response = await cls._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False
    
    @classmethod
    async def generate_response(
        cls,
        user_input: str,
        session_id: str,
        context: Optional[str] = None,
        personality: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a response using the LLM"""
        if not cls._client:
            raise RuntimeError("LLM service not initialized")
        
        try:
            # Build conversation history
            messages = cls._build_messages(user_input, session_id, context, personality)
            
            # Generate response
            response = await cls._client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=max_tokens or settings.openai_max_tokens,
                temperature=settings.openai_temperature,
                stream=False
            )
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Update conversation history
            cls._update_conversation_history(session_id, user_input, response_content)
            
            # Analyze response for animation triggers
            animation_data = cls._analyze_response_for_animation(response_content)
            
            return {
                "response": response_content,
                "animation": animation_data,
                "session_id": session_id,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    @classmethod
    def _build_messages(
        cls,
        user_input: str,
        session_id: str,
        context: Optional[str] = None,
        personality: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build the message list for the LLM"""
        messages = []
        
        # System message with personality and context
        system_content = "You are a helpful virtual human assistant."
        if personality:
            system_content += f" {personality}"
        if context:
            system_content += f" Context: {context}"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        if session_id in cls._conversation_history:
            for msg in cls._conversation_history[session_id][-10:]:  # Last 10 messages
                messages.append(msg)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    @classmethod
    def _update_conversation_history(
        cls,
        session_id: str,
        user_input: str,
        assistant_response: str
    ):
        """Update the conversation history for a session"""
        if session_id not in cls._conversation_history:
            cls._conversation_history[session_id] = []
        
        # Add user message
        cls._conversation_history[session_id].append({
            "role": "user",
            "content": user_input,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Add assistant message
        cls._conversation_history[session_id].append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep only last 20 messages to prevent memory issues
        if len(cls._conversation_history[session_id]) > 20:
            cls._conversation_history[session_id] = cls._conversation_history[session_id][-20:]
    
    @classmethod
    def _analyze_response_for_animation(cls, response: str) -> Dict[str, Any]:
        """Analyze the response to determine animation triggers"""
        animation_data = {
            "emotion": "neutral",
            "gestures": [],
            "facial_expression": "neutral",
            "speech_rate": "normal"
        }
        
        # Simple emotion detection based on keywords
        response_lower = response.lower()
        
        # Emotion detection
        if any(word in response_lower for word in ["happy", "great", "wonderful", "excellent"]):
            animation_data["emotion"] = "happy"
            animation_data["facial_expression"] = "smile"
        elif any(word in response_lower for word in ["sad", "sorry", "unfortunate", "regret"]):
            animation_data["emotion"] = "sad"
            animation_data["facial_expression"] = "frown"
        elif any(word in response_lower for word in ["excited", "amazing", "incredible"]):
            animation_data["emotion"] = "excited"
            animation_data["facial_expression"] = "wide_eyes"
        
        # Gesture detection
        if "?" in response:
            animation_data["gestures"].append("question_gesture")
        if any(word in response_lower for word in ["yes", "correct", "right"]):
            animation_data["gestures"].append("nod")
        if any(word in response_lower for word in ["no", "incorrect", "wrong"]):
            animation_data["gestures"].append("shake_head")
        
        # Speech rate detection
        if len(response.split()) > 50:
            animation_data["speech_rate"] = "fast"
        elif len(response.split()) < 10:
            animation_data["speech_rate"] = "slow"
        
        return animation_data
    
    @classmethod
    def get_conversation_history(cls, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return cls._conversation_history.get(session_id, [])
    
    @classmethod
    def clear_conversation_history(cls, session_id: str):
        """Clear conversation history for a session"""
        if session_id in cls._conversation_history:
            del cls._conversation_history[session_id]
    
    @classmethod
    def get_all_session_ids(cls) -> List[str]:
        """Get all active session IDs"""
        return list(cls._conversation_history.keys()) 