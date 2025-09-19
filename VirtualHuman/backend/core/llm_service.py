"""
LLM Service for Virtual Human API
Handles interactions with OpenAI and other LLM providers
"""

import logging
import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for managing LLM interactions"""
    
    _client: Optional[AsyncOpenAI] = None
    _is_healthy: bool = False
    _demo_mode: bool = False
    _conversation_history: List[Dict[str, str]] = []
    
    @classmethod
    async def initialize(cls):
        """Initialize the LLM service"""
        try:
            # Check if OpenAI API key is configured
            if not settings.openai.api_key or settings.openai.api_key == "your_openai_api_key_here":
                logger.warning("OpenAI API key not configured. Running in demo mode.")
                cls._client = None
                cls._is_healthy = True
                cls._demo_mode = True
                return
            
            # Initialize OpenAI client
            cls._client = AsyncOpenAI(api_key=settings.openai.api_key)
            cls._is_healthy = True
            cls._demo_mode = False
            logger.info("LLM service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            cls._is_healthy = False
            cls._demo_mode = True
    
    @classmethod
    async def cleanup(cls):
        """Cleanup resources"""
        cls._client = None
        cls._is_healthy = False
        logger.info("LLM service cleaned up")
    
    @classmethod
    def is_healthy(cls) -> bool:
        """Check if the service is healthy"""
        return cls._is_healthy
    
    @classmethod
    async def generate_response(
        cls, 
        user_input: str, 
        context: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a response using the LLM"""
        try:
            if cls._demo_mode:
                # Return demo response
                demo_response = cls._generate_demo_response(user_input)
                cls._update_conversation_history(user_input, demo_response)
                return {
                    "response": demo_response,
                    "animation_triggers": cls._analyze_response_for_animation(demo_response),
                    "session_id": session_id,
                    "mode": "demo"
                }
            
            if not cls._client:
                raise ValueError("LLM client not initialized")
            
            # Build messages for the API call
            messages = cls._build_messages(user_input, context)
            
            # Call OpenAI API
            response = await cls._client.chat.completions.create(
                model=settings.openai.model,
                messages=messages,
                max_tokens=settings.openai.max_tokens,
                temperature=settings.openai.temperature
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Update conversation history
            cls._update_conversation_history(user_input, response_text)
            
            return {
                "response": response_text,
                "animation_triggers": cls._analyze_response_for_animation(response_text),
                "session_id": session_id,
                "mode": "production"
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback to demo mode
            demo_response = cls._generate_demo_response(user_input)
            cls._update_conversation_history(user_input, demo_response)
            return {
                "response": demo_response,
                "animation_triggers": cls._analyze_response_for_animation(demo_response),
                "session_id": session_id,
                "mode": "fallback",
                "error": str(e)
            }
    
    @classmethod
    def _build_messages(cls, user_input: str, context: Optional[str] = None) -> List[Dict[str, str]]:
        """Build messages for the API call"""
        messages = []
        
        # Add system message
        system_message = (
            "You are a helpful virtual human tutor. "
            "Provide clear, engaging, and educational responses. "
            "Use a friendly and conversational tone."
        )
        if context:
            system_message += f" Context: {context}"
        
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history (last 10 messages)
        for msg in cls._conversation_history[-10:]:
            messages.append(msg)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    @classmethod
    def _update_conversation_history(cls, user_input: str, response: str):
        """Update conversation history"""
        cls._conversation_history.append({"role": "user", "content": user_input})
        cls._conversation_history.append({"role": "assistant", "content": response})
        
        # Keep only last 20 messages to prevent memory issues
        if len(cls._conversation_history) > 20:
            cls._conversation_history = cls._conversation_history[-20:]
    
    @classmethod
    def _analyze_response_for_animation(cls, response: str) -> Dict[str, Any]:
        """Analyze response to determine animation triggers"""
        triggers = {
            "gestures": [],
            "facial_expressions": [],
            "body_movements": []
        }
        
        # Simple keyword-based analysis
        response_lower = response.lower()
        
        # Gesture triggers
        if "hello" in response_lower or "hi" in response_lower:
            triggers["gestures"].append("wave")
        if "yes" in response_lower or "correct" in response_lower:
            triggers["gestures"].append("thumbs_up")
        if "no" in response_lower or "incorrect" in response_lower:
            triggers["gestures"].append("shake_head")
        
        # Facial expression triggers
        if "happy" in response_lower or "great" in response_lower:
            triggers["facial_expressions"].append("smile")
        if "think" in response_lower or "hmm" in response_lower:
            triggers["facial_expressions"].append("thinking")
        
        # Body movement triggers
        if "explain" in response_lower or "show" in response_lower:
            triggers["body_movements"].append("point")
        
        return triggers
    
    @classmethod
    def _generate_demo_response(cls, user_input: str) -> str:
        """Generate a demo response when API is not available"""
        user_input_lower = user_input.lower()
        
        if "hello" in user_input_lower or "hi" in user_input_lower:
            return "Hello! I'm your virtual tutor. I'm currently running in demo mode. How can I help you learn today?"
        elif "math" in user_input_lower or "calculate" in user_input_lower:
            return "I'd be happy to help you with math! In demo mode, I can explain concepts and provide examples. What specific math topic would you like to explore?"
        elif "science" in user_input_lower:
            return "Science is fascinating! I can help explain scientific concepts, theories, and discoveries. What area of science interests you?"
        elif "history" in user_input_lower:
            return "History is full of amazing stories and lessons! I can help you explore different historical periods and events. What would you like to learn about?"
        elif "help" in user_input_lower:
            return "I'm here to help you learn! I can assist with various subjects like math, science, history, language arts, and more. What would you like to study?"
        else:
            return f"That's an interesting question about '{user_input}'! I'm currently running in demo mode, but I'd be happy to help you learn about this topic. Could you tell me more about what specifically you'd like to know?"
    
    @classmethod
    def get_conversation_history(cls) -> List[Dict[str, str]]:
        """Get conversation history"""
        return cls._conversation_history.copy()
    
    @classmethod
    def clear_conversation_history(cls):
        """Clear conversation history"""
        cls._conversation_history.clear()
        logger.info("Conversation history cleared") 