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
import re
from pdf_utils import extract_text_from_pdf, get_pdf_metadata, is_pdf_file
from python_interpreter import ConstitutionAgent
from direct_langflow import DirectLangflowClient
from langflow_registry import LangflowFlowRegistry

app = FastAPI()

# Chart detection and prompting functions
def is_chart_request(message: str) -> bool:
    """Detect if the user is asking for a chart or visualization"""
    chart_keywords = [
        'chart', 'graph', 'plot', 'visualization', 'visualize', 'diagram',
        'bar chart', 'line chart', 'pie chart', 'scatter plot', 'histogram',
        'show data', 'display data', 'create a chart', 'make a graph',
        'data visualization', 'plot the data', 'chart the data'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in chart_keywords)

def get_chart_prompt(message: str) -> str:
    """Enhance the user message with chart formatting instructions"""
    chart_instructions = """

IMPORTANT: Since you're asking for a chart/visualization, please provide your response in the following Chart.js JSON format:

```chart
{
  "type": "bar|line|pie|doughnut",
  "title": "Chart Title",
  "data": {
    "labels": ["Label1", "Label2", "Label3"],
    "datasets": [{
      "label": "Dataset Label",
      "data": [value1, value2, value3],
      "backgroundColor": "rgba(54, 162, 235, 0.6)",
      "borderColor": "rgba(54, 162, 235, 1)",
      "borderWidth": 1
    }]
  }
}
```

Chart types available:
- "bar": Bar chart for comparing categories
- "line": Line chart for trends over time  
- "pie": Pie chart for proportions
- "doughnut": Doughnut chart for proportions with center space

EXAMPLES:

Bar Chart Example:
```chart
{
  "type": "bar",
  "title": "Sales by Month",
  "data": {
    "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
    "datasets": [{
      "label": "Sales",
      "data": [12000, 19000, 15000, 25000, 22000],
      "backgroundColor": "rgba(54, 162, 235, 0.6)",
      "borderColor": "rgba(54, 162, 235, 1)",
      "borderWidth": 1
    }]
  }
}
```

Line Chart Example:
```chart
{
  "type": "line",
  "title": "Website Traffic",
  "data": {
    "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
    "datasets": [{
      "label": "Visitors",
      "data": [1000, 1200, 1100, 1400],
      "backgroundColor": "rgba(75, 192, 192, 0.2)",
      "borderColor": "rgba(75, 192, 192, 1)",
      "borderWidth": 2
    }]
  }
}
```

Pie Chart Example:
```chart
{
  "type": "pie",
  "title": "Market Share",
  "data": {
    "labels": ["Product A", "Product B", "Product C"],
    "datasets": [{
      "data": [40, 35, 25],
      "backgroundColor": [
        "rgba(255, 99, 132, 0.6)",
        "rgba(54, 162, 235, 0.6)",
        "rgba(255, 205, 86, 0.6)"
      ]
    }]
  }
}
```

Please provide both the chart data in the above format AND a brief explanation of the visualization.

"""
    
    return message + chart_instructions

def determine_animation_from_response(response_content: str) -> str:
    """Determine appropriate animation based on response content"""
    content_lower = response_content.lower()
    
    # Chart-related animations
    if any(keyword in content_lower for keyword in ['chart', 'graph', 'visualization', 'plot']):
        return "excited"
    
    # Error-related animations
    if any(keyword in content_lower for keyword in ['error', 'sorry', 'unable', 'cannot', 'failed']):
        return "concerned"
    
    # Success/completion animations
    if any(keyword in content_lower for keyword in ['success', 'completed', 'done', 'finished', 'ready']):
        return "happy"
    
    # Question/thinking animations
    if any(keyword in content_lower for keyword in ['?', 'what', 'how', 'why', 'when', 'where']):
        return "curious"
    
    # Excitement indicators
    if any(keyword in content_lower for keyword in ['!', 'amazing', 'great', 'excellent', 'wonderful', 'fantastic']):
        return "excited"
    
    # Greeting animations
    if any(keyword in content_lower for keyword in ['hello', 'hi', 'hey', 'greetings', 'welcome']):
        return "wave"
    
    # Data/analysis animations
    if any(keyword in content_lower for keyword in ['data', 'analysis', 'results', 'statistics', 'report']):
        return "analytical"
    
    # Default thinking animation
    return "thinking"

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
        # Check if this is a chart request and enhance the prompt
        enhanced_message = req.message
        if is_chart_request(req.message):
            logger.info("Chart request detected, enhancing prompt with chart instructions")
            enhanced_message = get_chart_prompt(req.message)
        
        llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_key)
        response = await llm.ainvoke(enhanced_message)
        logger.info(f"OpenAI chat response: {response.content!r}")
        
        # Determine animation based on response content
        animation = determine_animation_from_response(response.content)
        logger.info(f"Determined animation: {animation}")
        
        # Generate audio if requested
        audio_url = None
        if req.use_voice and req.voice_id:
            audio_filename = await generate_speech(response.content, req.voice_id, openai_key)
            if audio_filename:
                audio_url = f"/api/audio/files/{audio_filename}"
        
        return {
            "response": response.content,
            "animation": animation,
            "audio_url": audio_url
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
        
        # Check if this is a chart request and enhance the prompt
        if is_chart_request(req.message):
            logger.info("Chart request detected in MCP, enhancing prompt with chart instructions")
            full_prompt = get_chart_prompt(full_prompt)
        
        response = await agent.run(full_prompt)
        logger.info(f"MCP response: {response!r}")
        
        # Determine animation based on response content
        animation = determine_animation_from_response(response)
        logger.info(f"Determined animation: {animation}")
        
        # Generate audio if requested
        audio_url = None
        if req.use_voice and req.voice_id:
            audio_filename = await generate_speech(response, req.voice_id, openai_key)
            if audio_filename:
                audio_url = f"/api/audio/files/{audio_filename}"
        
        return {
            "response": response,
            "animation": animation,
            "audio_url": audio_url
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

# PDF Processing Endpoints
@app.post("/api/pdf/extract")
async def extract_pdf_text(file_path: str):
    """Extract text from a PDF file"""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        if not is_pdf_file(file_path):
            raise HTTPException(status_code=400, detail="File is not a valid PDF")
        
        text = extract_text_from_pdf(file_path)
        if text is None:
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")
        
        return {
            "success": True,
            "text": text,
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/metadata")
async def get_pdf_info(file_path: str):
    """Get metadata from a PDF file"""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        if not is_pdf_file(file_path):
            raise HTTPException(status_code=400, detail="File is not a valid PDF")
        
        metadata = get_pdf_metadata(file_path)
        if metadata is None:
            raise HTTPException(status_code=500, detail="Failed to get PDF metadata")
        
        return {
            "success": True,
            "metadata": metadata,
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Constitution Agent Endpoints
constitution_agent = ConstitutionAgent()


# Langflow Flow Registry
flow_registry = LangflowFlowRegistry()

# Direct Langflow Client (no MCP) - Initialize with default flow from registry
default_flow = flow_registry.get_active_flow()
if default_flow:
    direct_langflow = DirectLangflowClient(
        host_url=default_flow["host_url"], 
        flow_id=default_flow["id"]
    )
else:
    direct_langflow = DirectLangflowClient()

@app.post("/api/constitution/execute")
async def execute_python_code(request: dict):
    """Execute Python code with constitutional principles"""
    try:
        code = request.get("code", "")
        context = request.get("context", "")
        
        if not code.strip():
            raise HTTPException(status_code=400, detail="Python code is required")
        
        result = constitution_agent.execute_python(code, context)
        
        return {
            "success": result["success"],
            "output": result["output"],
            "error": result["error"],
            "constitutional_guidance": result["constitutional_guidance"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing Python code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/constitution/info")
async def get_constitution_info():
    """Get Constitution Agent information"""
    try:
        info = constitution_agent.get_constitution_info()
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        logger.error(f"Error getting constitution info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/constitution/modules")
async def get_available_modules():
    """Get available Python modules"""
    try:
        modules = constitution_agent.interpreter.get_available_modules()
        return {
            "success": True,
            "modules": modules
        }
    except Exception as e:
        logger.error(f"Error getting modules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/constitution/add-module")
async def add_module(request: dict):
    """Add a new module to allowed modules"""
    try:
        module_name = request.get("module_name", "")
        
        if not module_name:
            raise HTTPException(status_code=400, detail="Module name is required")
        
        success = constitution_agent.interpreter.add_module(module_name)
        
        return {
            "success": success,
            "module_name": module_name,
            "message": f"Module {module_name} {'added successfully' if success else 'failed to add'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding module: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Direct Langflow API Endpoints (No MCP)
@app.post("/api/direct-langflow/chat")
async def direct_langflow_chat(request: dict):
    """Direct chat with Langflow (no MCP protocol)"""
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", "")
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message is required")
        
        result = await direct_langflow.chat_direct(message, session_id)
        
        return {
            "success": result["success"],
            "response": result.get("response", ""),
            "session_id": result.get("session_id", ""),
            "execution_time": result.get("execution_time", 0),
            "raw_outputs": result.get("raw_outputs", {}),
            "metadata": result.get("metadata", {}),
            "error": result.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with direct Langflow chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/direct-langflow/run")
async def direct_langflow_run(request: dict):
    """Direct Langflow flow execution (no MCP protocol)"""
    try:
        inputs = request.get("inputs", {})
        session_id = request.get("session_id", "")
        
        if not inputs:
            raise HTTPException(status_code=400, detail="Inputs are required")
        
        result = await direct_langflow.run_flow_direct(inputs, session_id)
        
        return {
            "success": result["success"],
            "outputs": result.get("outputs", {}),
            "session_id": result.get("session_id", ""),
            "execution_time": result.get("execution_time", 0),
            "metadata": result.get("metadata", {}),
            "error": result.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with direct Langflow run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/direct-langflow/health")
async def direct_langflow_health():
    """Check direct Langflow server health"""
    try:
        result = await direct_langflow.check_connection()
        return {
            "success": result["success"],
            "status": result["status"],
            "host_url": result["host_url"],
            "server_info": result.get("server_info", {}),
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"Error checking direct Langflow health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/direct-langflow/flows")
async def direct_langflow_flows():
    """Get available flows directly from Langflow"""
    try:
        result = await direct_langflow.get_available_flows_direct()
        return {
            "success": result["success"],
            "flows": result.get("flows", []),
            "count": result.get("count", 0),
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"Error getting direct Langflow flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/direct-langflow/flow-info")
async def direct_langflow_flow_info():
    """Get current flow information directly"""
    try:
        result = await direct_langflow.get_flow_info_direct()
        return {
            "success": result["success"],
            "flow_info": result.get("flow_info", {}),
            "flow_id": result.get("flow_id", ""),
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"Error getting direct flow info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/direct-langflow/info")
async def direct_langflow_info():
    """Get Direct Langflow Client information"""
    try:
        info = direct_langflow.get_client_info()
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        logger.error(f"Error getting direct Langflow info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Langflow Flow Registry Endpoints
@app.get("/api/langflow-flows")
async def get_all_flows():
    """Get all registered Langflow flows"""
    try:
        result = flow_registry.get_all_flows()
        # Add flow keys to each flow for frontend use
        flows_with_keys = {}
        for key, flow in result.get("flows", {}).items():
            flow_with_key = {**flow, "key": key}
            flows_with_keys[key] = flow_with_key
        
        return {
            "success": result["success"],
            "flows": flows_with_keys,
            "count": result["count"],
            "active_count": result["active_count"]
        }
    except Exception as e:
        logger.error(f"Error getting flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langflow-flows/register")
async def register_flow(request: dict):
    """Register a new Langflow flow"""
    try:
        flow_id = request.get("flow_id", "")
        name = request.get("name", "")
        description = request.get("description", "")
        host_url = request.get("host_url", "http://localhost:7860")
        category = request.get("category", "General")
        
        if not flow_id or not name:
            raise HTTPException(status_code=400, detail="flow_id and name are required")
        
        result = flow_registry.register_flow(flow_id, name, description, host_url, category)
        if result["success"]:
            # Add the flow key to the response
            flow_key = name.lower().replace(" ", "_").replace("-", "_")
            result["flow_key"] = flow_key
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langflow-flows/{flow_key}")
async def get_flow(flow_key: str):
    """Get a specific flow by key"""
    try:
        flow = flow_registry.get_flow(flow_key)
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow '{flow_key}' not found")
        return {"success": True, "flow": flow}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/langflow-flows/{flow_key}")
async def update_flow(flow_key: str, request: dict):
    """Update an existing flow"""
    try:
        updates = {k: v for k, v in request.items() if k in ["name", "description", "host_url", "category", "is_active"]}
        if not updates:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        result = flow_registry.update_flow(flow_key, updates)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/langflow-flows/{flow_key}")
async def delete_flow(flow_key: str):
    """Delete a flow from registry"""
    try:
        result = flow_registry.delete_flow(flow_key)
        return result
    except Exception as e:
        logger.error(f"Error deleting flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langflow-flows/{flow_key}/activate")
async def activate_flow(flow_key: str):
    """Activate a specific flow and update the client"""
    try:
        # Get flow details
        flow = flow_registry.get_flow(flow_key)
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow '{flow_key}' not found")
        
        # Update client configuration
        direct_langflow.set_flow_id(flow["id"])
        direct_langflow.set_host_url(flow["host_url"])
        
        # Clear current session when switching flows
        direct_langflow.clear_session()
        
        # Update registry
        result = flow_registry.set_active_flow(flow_key)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langflow-flows/{flow_key}/test")
async def test_flow_connection(flow_key: str):
    """Test connection to a specific flow"""
    try:
        result = flow_registry.test_flow_connection(flow_key)
        return result
    except Exception as e:
        logger.error(f"Error testing flow connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langflow-flows/categories")
async def get_flow_categories():
    """Get all flow categories"""
    try:
        categories = flow_registry.get_categories()
        return {"success": True, "categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langflow-flows/search")
async def search_flows(query: str):
    """Search flows by name or description"""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        flows = flow_registry.search_flows(query)
        return {"success": True, "flows": flows, "count": len(flows)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langflow-flows/active")
async def get_active_flow():
    """Get the currently active flow"""
    try:
        active_flow = flow_registry.get_active_flow()
        if not active_flow:
            return {"success": False, "message": "No active flow found"}
        
        return {"success": True, "flow": active_flow}
    except Exception as e:
        logger.error(f"Error getting active flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langflow-flows/current-config")
async def get_current_flow_config():
    """Get the current flow configuration from the client"""
    try:
        config = direct_langflow.get_current_config()
        return {"success": True, "config": config}
    except Exception as e:
        logger.error(f"Error getting current flow config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Langflow Session Management Endpoints
@app.post("/api/langflow-session/start")
async def start_langflow_session():
    """Start a new Langflow session"""
    try:
        session_id = direct_langflow.start_new_session()
        return {
            "success": True,
            "session_id": session_id,
            "message": "New session started"
        }
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langflow-session/current")
async def get_current_session():
    """Get the current session ID"""
    try:
        session_id = direct_langflow.get_current_session_id()
        return {
            "success": True,
            "session_id": session_id,
            "has_session": session_id is not None
        }
    except Exception as e:
        logger.error(f"Error getting current session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langflow-session/clear")
async def clear_langflow_session():
    """Clear the current Langflow session"""
    try:
        direct_langflow.clear_session()
        return {
            "success": True,
            "message": "Session cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langflow-session/set")
async def set_langflow_session(request: dict):
    """Set a specific session ID"""
    try:
        session_id = request.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        direct_langflow.set_session_id(session_id)
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session ID set"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 