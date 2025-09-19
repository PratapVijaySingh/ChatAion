from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
from core.llm_service import LLMService
from core.audio_service import AudioService
from core.animation_service import AnimationService

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: str
    context: Optional[str] = None
    personality: Optional[str] = None
    use_voice: bool = False
    voice_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    animation: Dict[str, Any]
    audio_url: Optional[str] = None
    timestamp: float

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    message_count: int
    created_at: float
    last_activity: float

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the virtual human"""
    try:
        # Generate LLM response
        llm_result = await LLMService.generate_response(
            user_input=request.message,
            session_id=request.session_id,
            context=request.context,
            personality=request.personality
        )
        
        # Create animation data
        animation_data = await AnimationService.create_complete_animation(
            blendshapes=llm_result["animation"].get("blendshapes", {}),
            gestures=llm_result["animation"].get("gestures", []),
            emotion=llm_result["animation"].get("emotion", "neutral")
        )
        
        # Send animation to Unity if connected
        await AnimationService.send_animation_data(animation_data)
        
        # Generate audio if requested
        audio_url = None
        if request.use_voice:
            audio_result = await AudioService.create_audio_response(
                text=llm_result["response"],
                voice_id=request.voice_id,
                emotion=llm_result["animation"].get("emotion", "neutral")
            )
            # In a real implementation, you'd save the audio and return a URL
            audio_url = f"/api/audio/play/{request.session_id}"
        
        return ChatResponse(
            response=llm_result["response"],
            session_id=request.session_id,
            animation=animation_data,
            audio_url=audio_url,
            timestamp=llm_result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error in chat send: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions():
    """Get all active chat sessions"""
    try:
        session_ids = LLMService.get_all_session_ids()
        sessions = []
        
        for session_id in session_ids:
            history = LLMService.get_conversation_history(session_id)
            if history:
                sessions.append(SessionInfo(
                    session_id=session_id,
                    message_count=len(history),
                    created_at=history[0]["timestamp"] if history else 0,
                    last_activity=history[-1]["timestamp"] if history else 0
                ))
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a specific session"""
    try:
        history = LLMService.get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    try:
        LLMService.clear_conversation_history(session_id)
        return {"message": f"Session {session_id} cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            try:
                llm_result = await LLMService.generate_response(
                    user_input=message_data["message"],
                    session_id=session_id,
                    context=message_data.get("context"),
                    personality=message_data.get("personality")
                )
                
                # Create animation data
                animation_data = await AnimationService.create_complete_animation(
                    blendshapes=llm_result["animation"].get("blendshapes", {}),
                    gestures=llm_result["animation"].get("gestures", []),
                    emotion=llm_result["animation"].get("emotion", "neutral")
                )
                
                # Send animation to Unity
                await AnimationService.send_animation_data(animation_data)
                
                # Send response back to client
                response = {
                    "type": "chat_response",
                    "response": llm_result["response"],
                    "animation": animation_data,
                    "timestamp": llm_result["timestamp"]
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                error_response = {
                    "type": "error",
                    "error": str(e)
                }
                await websocket.send_text(json.dumps(error_response))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.close()
        except:
            pass 