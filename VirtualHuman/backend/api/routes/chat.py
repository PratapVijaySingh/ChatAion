"""
Chat API routes for Virtual Human
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import json
import logging

from core.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for demo purposes
sessions = {}
conversation_history = {}

@router.post("/send")
async def send_message(message_data: Dict[str, Any]):
    """Send a message and get response"""
    try:
        user_input = message_data.get("message", "")
        session_id = message_data.get("session_id", "default")
        
        if not user_input:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Generate response using LLM service
        response = await LLMService.generate_response(
            user_input=user_input,
            session_id=session_id
        )
        
        # Store in conversation history
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        conversation_history[session_id].append({
            "user": user_input,
            "assistant": response["response"]
        })
        
        return {
            "response": response["response"],
            "animation_triggers": response.get("animation_triggers", {}),
            "session_id": session_id,
            "mode": response.get("mode", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_sessions():
    """Get all active sessions"""
    return {
        "sessions": list(sessions.keys()),
        "total": len(sessions)
    }

@router.get("/history/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    if session_id not in conversation_history:
        return {"messages": [], "session_id": session_id}
    
    return {
        "messages": conversation_history[session_id],
        "session_id": session_id
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its history"""
    if session_id in sessions:
        del sessions[session_id]
    if session_id in conversation_history:
        del conversation_history[session_id]
    
    return {"message": f"Session {session_id} deleted successfully"}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Generate response
            response = await LLMService.generate_response(
                user_input=message_data.get("message", ""),
                session_id=session_id
            )
            
            # Send response back
            await websocket.send_text(json.dumps({
                "response": response["response"],
                "animation_triggers": response.get("animation_triggers", {}),
                "session_id": session_id,
                "mode": response.get("mode", "unknown")
            }))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "error": str(e),
                "session_id": session_id
            }))
        except:
            pass 