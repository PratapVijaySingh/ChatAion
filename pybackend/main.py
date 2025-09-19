from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
from mcp_use import MCPAgent, MCPClient
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import json
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import logging
import tempfile
import openai
import time

app = FastAPI()

# Enable CORS for all origins and methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MCP_FILE = "mcps.json"

# Audio directory
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Serve static files
app.mount("/api/audio/files", StaticFiles(directory=AUDIO_DIR), name="audio")

class MCP(BaseModel):
    id: str
    name: str
    command: str
    args: List[str]

class LLMRequest(BaseModel):
    prompt: str
    mcp_id: Optional[str] = None
    openai_key: str
    history: Optional[List[Dict[str, Any]]] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    use_voice: bool = False
    voice_id: Optional[str] = None
    mcp_server: Optional[str] = None
    server_type: Optional[str] = None
    openai_key: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None

# Helper functions for MCPs

def read_mcps():
    if not os.path.exists(MCP_FILE):
        return []
    with open(MCP_FILE, "r") as f:
        return json.load(f)

def write_mcps(mcps):
    with open(MCP_FILE, "w") as f:
        json.dump(mcps, f, indent=2)

@app.get("/api/mcps")
def list_mcps():
    return read_mcps()

@app.post("/api/mcps")
def add_mcp(mcp: MCP):
    mcps = read_mcps()
    if any(m["id"] == mcp.id for m in mcps):
        raise HTTPException(status_code=400, detail="MCP with this id already exists")
    mcps.append(mcp.dict())
    write_mcps(mcps)
    return mcp

@app.put("/api/mcps/{mcp_id}")
def update_mcp(mcp_id: str, mcp: MCP):
    mcps = read_mcps()
    for i, m in enumerate(mcps):
        if m["id"] == mcp_id:
            mcps[i] = mcp.dict()
            write_mcps(mcps)
            return mcp
    raise HTTPException(status_code=404, detail="MCP not found")

@app.delete("/api/mcps/{mcp_id}")
def delete_mcp(mcp_id: str):
    mcps = read_mcps()
    for i, m in enumerate(mcps):
        if m["id"] == mcp_id:
            deleted = mcps.pop(i)
            write_mcps(mcps)
            return deleted
    raise HTTPException(status_code=404, detail="MCP not found")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pybackend")

# TTS Functions
async def generate_speech(text: str, voice_id: str, openai_key: str) -> Optional[str]:
    """Generate speech using OpenAI TTS API"""
    try:
        client = openai.OpenAI(api_key=openai_key)
        
        # Map voice_id to OpenAI voice names
        voice_mapping = {
            'alloy': 'alloy',
            'echo': 'echo', 
            'fable': 'fable',
            'onyx': 'onyx',
            'nova': 'nova',
            'shimmer': 'shimmer'
        }
        
        openai_voice = voice_mapping.get(voice_id, 'alloy')
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=openai_voice,
            input=text
        )
        
        # Generate unique filename
        filename = f"speech_{int(time.time() * 1000)}_{voice_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Save to audio directory
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filename  # Return just the filename, not full path
            
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return None

@app.post("/api/llm")
async def llm_endpoint(req: LLMRequest):
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = req.openai_key
    logger.info(f"Received /api/llm request: prompt={req.prompt!r}, mcp_id={req.mcp_id}")
    # If no mcp_id, call OpenAI directly
    if not req.mcp_id:
        logger.info("No mcp_id provided, using OpenAI directly.")
        llm = ChatOpenAI(model="gpt-4o", openai_api_key=req.openai_key)
        response = await llm.ainvoke(req.prompt)
        logger.info(f"OpenAI response: {response.content!r}")
        return {"reply": response.content}
    # Otherwise, use selected MCP
    mcps = read_mcps()
    mcp = next((m for m in mcps if m["id"] == req.mcp_id), None)
    if not mcp:
        logger.error(f"MCP with id {req.mcp_id} not found.")
        raise HTTPException(status_code=404, detail="MCP not found")
    try:
        logger.info(f"Starting MCPClient with command: {mcp['command']} {mcp['args']}")
        # Write a temporary config file for this MCP
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
            config_dict = {
                "mcpServers": {
                    mcp["id"]: {
                        "command": mcp["command"],
                        "args": mcp["args"]
                    }
                }
            }
            import json as _json
            _json.dump(config_dict, tmp)
            tmp.flush()
            client = MCPClient.from_config_file(tmp.name)
        llm = ChatOpenAI(model="gpt-4o", openai_api_key=req.openai_key)
        agent = MCPAgent(llm=llm, client=client, max_steps=15, memory_enabled=True)
        # Concatenate history into the prompt for context
        if req.history:
            context = ""
            for msg in req.history:
                if msg["role"] == "user":
                    context += f"User: {msg['text']}\n"
                elif msg["role"] == "llm":
                    context += f"Assistant: {msg['text']}\n"
                elif msg["role"] == "system":
                    context += f"System: {msg['text']}\n"
            full_prompt = context + f"User: {req.prompt}"
        else:
            full_prompt = req.prompt
        response = await agent.run(full_prompt)
        logger.info(f"MCP response: {response!r}")
        return {"reply": response}
    except Exception as e:
        logger.error(f"MCP error: {e}", exc_info=True)
        # Fallback to OpenAI
        llm = ChatOpenAI(model="gpt-4o", openai_api_key=req.openai_key)
        response = await llm.ainvoke(req.prompt)
        logger.info(f"Fallback OpenAI response: {response.content!r}")
        return {"reply": response.content, "fallback": True, "error": str(e)}

@app.post("/api/chat/send")
async def chat_send(req: ChatRequest):
    """Direct OpenAI chat endpoint"""
    load_dotenv()
    
    # Get API key from request or environment
    openai_key = req.openai_key or os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not provided")
    
    logger.info(f"Received /api/chat/send request: message={req.message!r}")
    
    try:
        llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_key)
        response = await llm.ainvoke(req.message)
        logger.info(f"OpenAI chat response: {response.content!r}")
        
        return {
            "response": response.content,
            "animation": "thinking",  # Default animation
            "audio_url": None  # No audio for now
        }
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcp/send")
async def mcp_send(req: ChatRequest):
    """MCP server chat endpoint"""
    load_dotenv()
    
    # Get API key from request or environment
    openai_key = req.openai_key or os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not provided")
    
    logger.info(f"Received /api/mcp/send request: message={req.message!r}, mcp_server={req.mcp_server}")
    
    # If no mcp_server specified, fallback to direct OpenAI
    if not req.mcp_server:
        return await chat_send(req)
    
    # If mcp_server is "openai", use direct OpenAI chat
    if req.mcp_server == "openai":
        return await chat_send(req)
    
    try:
        # Get MCP configuration
        mcps = read_mcps()
        mcp = next((m for m in mcps if m["id"] == req.mcp_server), None)
        
        if not mcp:
            logger.warning(f"MCP {req.mcp_server} not found, falling back to OpenAI")
            return await chat_send(req)
        
        # Create MCP client
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
            config_dict = {
                "mcpServers": {
                    mcp["id"]: {
                        "command": mcp["command"],
                        "args": mcp["args"]
                    }
                }
            }
            import json as _json
            _json.dump(config_dict, tmp)
            tmp.flush()
            client = MCPClient.from_config_file(tmp.name)
        
        llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_key)
        agent = MCPAgent(llm=llm, client=client, max_steps=15, memory_enabled=True)
        
        # Build conversation context with history
        if req.history:
            context = ""
            for msg in req.history:
                if msg.get("role") == "user":
                    context += f"User: {msg.get('content', '')}\n"
                elif msg.get("role") == "assistant":
                    context += f"Assistant: {msg.get('content', '')}\n"
            full_prompt = context + f"User: {req.message}"
        else:
            full_prompt = req.message
        
        response = await agent.run(full_prompt)
        logger.info(f"MCP response: {response!r}")
        
        return {
            "response": response,
            "animation": "thinking",
            "audio_url": None
        }
        
    except Exception as e:
        logger.error(f"MCP error: {e}", exc_info=True)
        # Fallback to direct OpenAI
        return await chat_send(req)

# Mock endpoints for frontend compatibility
@app.get("/api/avatar/presets")
def get_avatar_presets():
    """Mock avatar presets endpoint"""
    return [
        {"preset_id": "default", "name": "Default Avatar"},
        {"preset_id": "professional", "name": "Professional"},
        {"preset_id": "casual", "name": "Casual"},
        {"preset_id": "friendly", "name": "Friendly"}
    ]

@app.get("/api/audio/voices")
def get_audio_voices():
    """Audio voices endpoint"""
    return {
        "openai": [
            {"voice_id": "alloy", "name": "Alloy"},
            {"voice_id": "echo", "name": "Echo"},
            {"voice_id": "fable", "name": "Fable"},
            {"voice_id": "onyx", "name": "Onyx"},
            {"voice_id": "nova", "name": "Nova"},
            {"voice_id": "shimmer", "name": "Shimmer"}
        ],
        "elevenlabs": [],
        "azure": []
    }

@app.post("/api/audio/generate")
async def generate_speech_endpoint(req: dict):
    """Generate speech from text"""
    try:
        text = req.get("text", "")
        voice_id = req.get("voice_id", "alloy")
        openai_key = req.get("openai_key", "")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        if not openai_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        logger.info(f"Speech generation requested: text={text[:50]}..., voice={voice_id}")
        
        # Generate actual speech using OpenAI TTS
        audio_filename = await generate_speech(text, voice_id, openai_key)
        
        if audio_filename:
            return {
                "success": True,
                "audio_url": f"/api/audio/files/{audio_filename}",
                "filename": audio_filename,
                "text": text,
                "voice_id": voice_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
            
    except Exception as e:
        logger.error(f"Speech generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 