from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
from typing import List, Optional, Dict, Any
import logging
import tempfile
import openai
import shutil
import requests
import uuid
import time
import base64
import io
# from langchain_openai import ChatOpenAI  # Commented out due to import issues

app = FastAPI()

# Enable CORS for all origins and methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_backend")

# Load environment variables
load_dotenv()

# Audio directory
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Serve static files
app.mount("/api/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    use_voice: bool = False
    voice_id: Optional[str] = None
    openai_key: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None

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

async def create_custom_voice_elevenlabs(name: str, audio_file_path: str, api_key: str) -> Optional[str]:
    """Create a custom voice using ElevenLabs API"""
    try:
        url = "https://api.elevenlabs.io/v1/voices/add"
        
        logger.info(f"Making request to ElevenLabs API: {url}")
        logger.info(f"API key length: {len(api_key) if api_key else 0}")
        
        headers = {
            "Accept": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "name": name,
            "description": f"Custom voice: {name}"
        }
        
        logger.info(f"Request data: {data}")
        
        # Check if file exists and get size
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file does not exist: {audio_file_path}")
            return None
        
        file_size = os.path.getsize(audio_file_path)
        logger.info(f"Audio file size: {file_size} bytes")
        
        with open(audio_file_path, "rb") as audio_file:
            files = {
                "files": audio_file
            }
            
            logger.info("Sending request to ElevenLabs...")
            response = requests.post(url, headers=headers, data=data, files=files, timeout=60)
        
        logger.info(f"ElevenLabs response status: {response.status_code}")
        logger.info(f"ElevenLabs response text: {response.text}")
        
        if response.status_code == 200:
            voice_data = response.json()
            voice_id = voice_data.get("voice_id")
            logger.info(f"Successfully created voice with ID: {voice_id}")
            return voice_id
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating custom voice with ElevenLabs: {e}", exc_info=True)
        return None

async def generate_speech_azure(text: str, voice_name: str, api_key: str, region: str = "eastus") -> Optional[str]:
    """Generate speech using Azure Cognitive Services TTS"""
    try:
        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
        }
        
        # Create SSML for Azure TTS
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
            <voice name='{voice_name}'>
                {text}
            </voice>
        </speak>
        """
        
        response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))
        
        if response.status_code == 200:
            # Generate unique filename
            filename = f"azure_speech_{int(time.time() * 1000)}_{voice_name.replace(' ', '_')}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            
            # Save to audio directory
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filename
        else:
            logger.error(f"Azure TTS error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating speech with Azure: {e}")
        return None

async def create_custom_voice_azure(name: str, audio_file_path: str, api_key: str, region: str = "eastus") -> Optional[str]:
    """Create a custom voice using Azure Cognitive Services (simplified version)"""
    try:
        # For Azure, we'll use a simplified approach since custom voice training
        # requires more complex setup. We'll return a mock voice ID for now.
        logger.info(f"Azure custom voice creation requested for: {name}")
        
        # In a real implementation, you would:
        # 1. Upload the audio file to Azure Blob Storage
        # 2. Create a custom voice model using Azure Speech Studio
        # 3. Train the model
        # 4. Deploy the model
        
        # For now, we'll return a mock voice ID
        mock_voice_id = f"azure_custom_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created mock Azure custom voice ID: {mock_voice_id}")
        
        return mock_voice_id
        
    except Exception as e:
        logger.error(f"Error creating custom voice with Azure: {e}")
        return None

async def generate_speech_custom_voice(text: str, voice_id: str, provider: str, api_key: str) -> Optional[str]:
    """Generate speech using custom voice"""
    try:
        if provider == "elevenlabs":
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Generate unique filename
                filename = f"custom_speech_{int(time.time() * 1000)}_{voice_id}.mp3"
                filepath = os.path.join(AUDIO_DIR, filename)
                
                # Save to audio directory
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return filename
            else:
                logger.error(f"ElevenLabs TTS error: {response.status_code} - {response.text}")
                return None
        elif provider == "azure":
            # For Azure, we'll use a standard voice since custom voice training is complex
            # You can replace this with your preferred Azure voice
            azure_voice = "en-US-AriaNeural"  # High-quality neural voice
            return await generate_speech_azure(text, azure_voice, api_key)
        else:
            logger.error(f"Unsupported provider: {provider}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating speech with custom voice: {e}")
        return None

# Basic endpoints
@app.get("/")
def read_root():
    return {"message": "Voice Backend API is running"}

@app.get("/api/test")
def test_endpoint():
    return {"message": "Backend is working", "status": "ok"}

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
    """Get available voices from different providers"""
    return {
        "openai": [
            {"voice_id": "alloy", "name": "Alloy"},
            {"voice_id": "echo", "name": "Echo"},
            {"voice_id": "fable", "name": "Fable"},
            {"voice_id": "onyx", "name": "Onyx"},
            {"voice_id": "nova", "name": "Nova"},
            {"voice_id": "shimmer", "name": "Shimmer"}
        ],
        "azure": [
            {"voice_id": "en-US-AriaNeural", "name": "Aria (Neural)"},
            {"voice_id": "en-US-JennyNeural", "name": "Jenny (Neural)"},
            {"voice_id": "en-US-GuyNeural", "name": "Guy (Neural)"},
            {"voice_id": "en-US-DavisNeural", "name": "Davis (Neural)"},
            {"voice_id": "en-US-AmberNeural", "name": "Amber (Neural)"},
            {"voice_id": "en-US-AnaNeural", "name": "Ana (Neural)"}
        ]
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
        
        audio_filename = await generate_speech(text, voice_id, openai_key)
        
        if audio_filename:
            return {
                "success": True,
                "audio_url": f"/api/audio/{audio_filename}",
                "filename": audio_filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
            
    except Exception as e:
        logger.error(f"Speech generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

@app.post("/api/audio/generate-azure")
async def generate_speech_azure_endpoint(req: dict):
    """Generate speech using Azure TTS"""
    try:
        text = req.get("text", "")
        voice_name = req.get("voice_name", "en-US-AriaNeural")
        api_key = req.get("api_key", "")
        region = req.get("region", "eastus")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="Azure API key is required")
        
        audio_filename = await generate_speech_azure(text, voice_name, api_key, region)
        
        if audio_filename:
            return {
                "success": True,
                "audio_url": f"/api/audio/{audio_filename}",
                "filename": audio_filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech with Azure")
            
    except Exception as e:
        logger.error(f"Azure speech generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Azure speech generation failed: {str(e)}")

@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    """Serve audio files"""
    filepath = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")

# Custom Voice Training Endpoints

@app.post("/api/voice/upload")
async def upload_voice_sample(
    file: UploadFile = File(...),
    name: str = Form(None),
    provider: str = Form("elevenlabs"),
    api_key: str = Form(None)
):
    """Upload voice sample for custom voice training"""
    try:
        logger.info(f"Received upload request: name={name}, provider={provider}, api_key={'***' if api_key else 'None'}")
        
        if not name:
            name = f"Custom Voice {uuid.uuid4().hex[:8]}"
        
        if not api_key:
            logger.error("API key is missing")
            raise HTTPException(status_code=400, detail="API key is required")
        
        # Validate file type
        logger.info(f"File content type: {file.content_type}")
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Create voice samples directory
        voice_samples_dir = os.path.join(AUDIO_DIR, "voice_samples")
        logger.info(f"Creating directory: {voice_samples_dir}")
        os.makedirs(voice_samples_dir, exist_ok=True)
        
        # Save uploaded file
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'wav'
        filename = f"{name}_{uuid.uuid4().hex[:8]}.{file_extension}"
        filepath = os.path.join(voice_samples_dir, filename)
        
        logger.info(f"Saving file to: {filepath}")
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved voice sample to: {filepath}")
        
        # Create custom voice
        if provider == "elevenlabs":
            logger.info("Creating custom voice with ElevenLabs...")
            voice_id = await create_custom_voice_elevenlabs(name, filepath, api_key)
        elif provider == "azure":
            logger.info("Creating custom voice with Azure...")
            voice_id = await create_custom_voice_azure(name, filepath, api_key)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        if voice_id:
            # Store voice info (in a real app, you'd use a database)
            voice_info = {
                "voice_id": voice_id,
                "name": name,
                "provider": provider,
                "status": "trained",
                "created_at": str(uuid.uuid4()),
                "file_path": filepath
            }
            
            # Save voice info to file (simple storage)
            voices_file = os.path.join(AUDIO_DIR, "custom_voices.json")
            voices = []
            if os.path.exists(voices_file):
                with open(voices_file, 'r') as f:
                    voices = json.load(f)
            
            voices.append(voice_info)
            
            with open(voices_file, 'w') as f:
                json.dump(voices, f, indent=2)
            
            logger.info(f"Custom voice created successfully: {voice_id}")
            return {
                "success": True,
                "voice_id": voice_id,
                "name": name,
                "message": "Custom voice created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create custom voice")
            
    except Exception as e:
        logger.error(f"Error uploading voice sample: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading voice sample: {str(e)}")

@app.get("/api/voice/custom")
def get_custom_voices():
    """Get list of custom voices"""
    try:
        voices_file = os.path.join(AUDIO_DIR, "custom_voices.json")
        if os.path.exists(voices_file):
            with open(voices_file, 'r') as f:
                voices = json.load(f)
            return voices
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting custom voices: {e}")
        return []

@app.post("/api/voice/generate-custom")
async def generate_speech_custom_endpoint(req: dict):
    """Generate speech using custom voice"""
    try:
        text = req.get("text", "")
        voice_id = req.get("voice_id", "")
        provider = req.get("provider", "elevenlabs")
        api_key = req.get("api_key", "")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        if not voice_id:
            raise HTTPException(status_code=400, detail="Voice ID is required")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        audio_filename = await generate_speech_custom_voice(text, voice_id, provider, api_key)
        
        if audio_filename:
            return {
                "success": True,
                "audio_url": f"/api/audio/{audio_filename}",
                "filename": audio_filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech with custom voice")
            
    except Exception as e:
        logger.error(f"Custom voice generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Custom voice generation failed: {str(e)}")

# Chat and MCP Endpoints

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
        client = openai.OpenAI(api_key=openai_key)
        
        # Build conversation history if provided
        if req.history:
            messages = []
            for msg in req.history:
                if msg.get("role") == "user":
                    messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("role") == "assistant":
                    messages.append({"role": "assistant", "content": msg.get("content", "")})
            
            # Add current message
            messages.append({"role": "user", "content": req.message})
            
            # Use OpenAI chat completion with history
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            response_content = response.choices[0].message.content
        else:
            # Single message without history
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": req.message}]
            )
            response_content = response.choices[0].message.content
        
        # Generate speech if requested
        audio_url = None
        if req.use_voice and req.voice_id:
            audio_filename = await generate_speech(response_content, req.voice_id, openai_key)
            if audio_filename:
                audio_url = f"/api/audio/{audio_filename}"
        
        return {
            "response": response_content,
            "animation": "thinking",  # Default animation
            "audio_url": audio_url
        }
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.post("/api/mcp/send")
async def mcp_send(req: ChatRequest):
    """MCP server chat endpoint (simplified - returns OpenAI response for now)"""
    load_dotenv()
    
    # Get API key from request or environment
    openai_key = req.openai_key or os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not provided")
    
    logger.info(f"Received /api/mcp/send request: message={req.message!r}")
    
    try:
        # For now, just use OpenAI directly since MCP modules are not available
        # In a full implementation, this would connect to MCP servers
        client = openai.OpenAI(api_key=openai_key)
        
        # Build conversation context if history is provided
        if req.history:
            messages = []
            for msg in req.history:
                if msg.get("role") == "user":
                    messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("role") == "assistant":
                    messages.append({"role": "assistant", "content": msg.get("content", "")})
            
            # Add current message
            messages.append({"role": "user", "content": req.message})
        else:
            messages = [{"role": "user", "content": req.message}]
        
        logger.info(f"Running MCP agent with message: {req.message}")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        response_content = response.choices[0].message.content
        logger.info(f"MCP response: {response_content!r}")
        
        # Generate speech if requested
        audio_url = None
        if req.use_voice and req.voice_id:
            audio_filename = await generate_speech(response_content, req.voice_id, openai_key)
            if audio_filename:
                audio_url = f"/api/audio/{audio_filename}"
        
        return {
            "response": response_content,
            "animation": "thinking",
            "audio_url": audio_url
        }
        
    except Exception as e:
        logger.error(f"MCP error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MCP error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
