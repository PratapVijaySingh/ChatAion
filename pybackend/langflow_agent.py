"""
Langflow Agent for ChatAion
Integrates with Langflow API for advanced AI workflows
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
import asyncio
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class LangflowAgent:
    """
    Langflow Agent - Integrates with Langflow API for advanced AI workflows
    """
    
    def __init__(self, host_url: str = "http://localhost:7860"):
        """
        Initialize Langflow Agent
        
        Args:
            host_url: Langflow server URL
        """
        self.host_url = host_url.rstrip('/')
        self.session = None
        self.flow_id = "bdad461a-0654-45e7-9e38-14fc48fb2063"
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def check_connection(self) -> Dict[str, Any]:
        """
        Check if Langflow server is accessible
        
        Returns:
            Connection status and server info
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.host_url}/api/v1/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "status": "connected",
                        "server_info": data,
                        "host_url": self.host_url
                    }
                else:
                    return {
                        "success": False,
                        "status": "error",
                        "error": f"HTTP {response.status}",
                        "host_url": self.host_url
                    }
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "host_url": self.host_url
            }
    
    async def get_flow_info(self) -> Dict[str, Any]:
        """
        Get information about the specific flow
        
        Returns:
            Flow information
        """
        try:
            session = await self._get_session()
            url = f"{self.host_url}/api/v1/flows/{self.flow_id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "flow_info": data,
                        "flow_id": self.flow_id
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "flow_id": self.flow_id
                    }
        except Exception as e:
            logger.error(f"Get flow info failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "flow_id": self.flow_id
            }
    
    async def run_flow(self, inputs: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the Langflow flow with given inputs
        
        Args:
            inputs: Input data for the flow
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Flow execution results
        """
        try:
            session = await self._get_session()
            url = f"{self.host_url}/api/v1/run/{self.flow_id}"
            
            payload = {
                "inputs": inputs,
                "tweaks": {},
                "session_id": session_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "outputs": data.get("outputs", {}),
                        "session_id": payload["session_id"],
                        "execution_time": data.get("execution_time", 0)
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "session_id": payload["session_id"]
                    }
        except Exception as e:
            logger.error(f"Run flow failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat_with_flow(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Chat with the Langflow flow using a message
        
        Args:
            message: User message
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Chat response from the flow
        """
        try:
            # Prepare inputs for the flow
            inputs = {
                "message": message,
                "user_id": "chat_user",
                "timestamp": datetime.now().isoformat()
            }
            
            # Run the flow
            result = await self.run_flow(inputs, session_id)
            
            if result["success"]:
                outputs = result["outputs"]
                return {
                    "success": True,
                    "response": outputs.get("response", "No response generated"),
                    "session_id": result["session_id"],
                    "execution_time": result["execution_time"],
                    "metadata": {
                        "flow_id": self.flow_id,
                        "timestamp": datetime.now().isoformat(),
                        "host_url": self.host_url
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "session_id": result.get("session_id")
                }
                
        except Exception as e:
            logger.error(f"Chat with flow failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_available_flows(self) -> Dict[str, Any]:
        """
        Get list of available flows from Langflow server
        
        Returns:
            List of available flows
        """
        try:
            session = await self._get_session()
            url = f"{self.host_url}/api/v1/flows"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "flows": data,
                        "count": len(data) if isinstance(data, list) else 0
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"Get flows failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_flow_schema(self) -> Dict[str, Any]:
        """
        Get the schema/inputs for the current flow
        
        Returns:
            Flow schema information
        """
        try:
            session = await self._get_session()
            url = f"{self.host_url}/api/v1/flows/{self.flow_id}/schema"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "schema": data,
                        "flow_id": self.flow_id
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "flow_id": self.flow_id
                    }
        except Exception as e:
            logger.error(f"Get flow schema failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "flow_id": self.flow_id
            }
    
    async def close(self):
        """Close the agent and cleanup resources"""
        await self._close_session()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the Langflow Agent"""
        return {
            "name": "Langflow Agent",
            "description": "Advanced AI workflows through Langflow integration",
            "host_url": self.host_url,
            "flow_id": self.flow_id,
            "capabilities": [
                "Chat with Langflow flows",
                "Execute AI workflows",
                "Session management",
                "Flow schema inspection",
                "Health monitoring"
            ],
            "endpoints": {
                "health": f"{self.host_url}/api/v1/health",
                "flows": f"{self.host_url}/api/v1/flows",
                "run_flow": f"{self.host_url}/api/v1/run/{self.flow_id}",
                "flow_schema": f"{self.host_url}/api/v1/flows/{self.flow_id}/schema"
            }
        }
