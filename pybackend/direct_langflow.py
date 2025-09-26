"""
Direct Langflow API Integration
Bypasses MCP and calls Langflow API directly
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
import asyncio
import aiohttp
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DirectLangflowClient:
    """
    Direct Langflow API Client - No MCP, direct API calls
    """
    
    def __init__(self, host_url: str = "http://localhost:7860"):
        """
        Initialize Direct Langflow Client
        
        Args:
            host_url: Langflow server URL
        """
        self.host_url = host_url.rstrip('/')
        self.flow_id = "b2636e6f-2c11-4274-b965-5bd98ca40336"
        self.session = None
        
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
        """Check if Langflow server is accessible"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.host_url}/api/v1/health") as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        return {
                            "success": True,
                            "status": "connected",
                            "server_info": data,
                            "host_url": self.host_url
                        }
                    except:
                        # If JSON parsing fails, server is running but not Langflow
                        return {
                            "success": True,
                            "status": "connected",
                            "server_info": {"message": "Server running but not Langflow API"},
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
    
    async def chat_direct(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Direct chat with Langflow - no MCP protocol
        
        Args:
            message: User message
            session_id: Optional session ID
            
        Returns:
            Direct response from Langflow
        """
        try:
            session = await self._get_session()
            url = f"{self.host_url}/api/v1/run/{self.flow_id}"
            
            payload = {
                "output_type": "chat",
                "input_type": "chat", 
                "input_value": message,
                "session_id": session_id or str(uuid.uuid4())
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        # If response is a list, take the first item
                        response_data = data[0] if data else {}
                    else:
                        response_data = data
                    
                    # Extract text content from Langflow JSON response
                    response_text = self._extract_langflow_text(response_data)
                    
                    # Debug logging
                    logger.info(f"🔍 Langflow response extraction:")
                    logger.info(f"  - Raw response_data type: {type(response_data)}")
                    logger.info(f"  - Raw response_data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                    logger.info(f"  - Full response_data: {response_data}")
                    logger.info(f"  - Extracted text: {response_text}")
                    logger.info(f"  - Session ID: {payload['session_id']}")
                    
                    return {
                        "success": True,
                        "response": response_text,
                        "session_id": payload["session_id"],
                        "execution_time": response_data.get("execution_time", 0) if isinstance(response_data, dict) else 0,
                        "raw_outputs": response_data.get("outputs", {}) if isinstance(response_data, dict) else response_data,
                        "metadata": {
                            "flow_id": self.flow_id,
                            "timestamp": datetime.now().isoformat(),
                            "host_url": self.host_url,
                            "method": "direct_api"
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "session_id": payload["session_id"]
                    }
        except Exception as e:
            logger.error(f"Direct chat failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_flow_direct(self, inputs: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Direct flow execution - no MCP protocol
        
        Args:
            inputs: Input data for the flow
            session_id: Optional session ID
            
        Returns:
            Direct flow execution results
        """
        try:
            session = await self._get_session()
            url = f"{self.host_url}/api/v1/run/{self.flow_id}"
            
            payload = {
                "output_type": "chat",
                "input_type": "chat",
                "input_value": inputs.get("message", str(inputs)),
                "session_id": session_id or str(uuid.uuid4())
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        # If response is a list, take the first item
                        response_data = data[0] if data else {}
                    else:
                        response_data = data
                    
                    return {
                        "success": True,
                        "outputs": response_data.get("outputs", {}) if isinstance(response_data, dict) else response_data,
                        "session_id": payload["session_id"],
                        "execution_time": response_data.get("execution_time", 0) if isinstance(response_data, dict) else 0,
                        "metadata": {
                            "flow_id": self.flow_id,
                            "timestamp": datetime.now().isoformat(),
                            "host_url": self.host_url,
                            "method": "direct_api"
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "session_id": payload["session_id"]
                    }
        except Exception as e:
            logger.error(f"Direct flow execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_flow_info_direct(self) -> Dict[str, Any]:
        """Get flow information directly"""
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
    
    async def get_available_flows_direct(self) -> Dict[str, Any]:
        """Get available flows directly"""
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
    
    def _extract_langflow_text(self, data):
        """Extract text content from Langflow response structure"""
        try:
            logger.info(f"Extracting text from data: {type(data)}")
            logger.info(f"Data structure: {str(data)[:500]}...")
            
            if isinstance(data, dict):
                # Handle the specific structure from your response:
                # outputs[0].outputs[0].results.message.data.text
                if "outputs" in data:
                    outputs = data["outputs"]
                    logger.info(f"Found outputs: {type(outputs)}")
                    
                    if isinstance(outputs, list) and len(outputs) > 0:
                        first_output = outputs[0]
                        logger.info(f"Processing first output: {type(first_output)}")
                        
                        if isinstance(first_output, dict) and "outputs" in first_output:
                            nested_outputs = first_output["outputs"]
                            logger.info(f"Found nested outputs: {type(nested_outputs)}")
                            
                            if isinstance(nested_outputs, list) and len(nested_outputs) > 0:
                                first_nested = nested_outputs[0]
                                logger.info(f"Processing first nested output: {type(first_nested)}")
                                
                                if isinstance(first_nested, dict) and "results" in first_nested:
                                    results = first_nested["results"]
                                    logger.info(f"Found results: {type(results)}")
                                    
                                    if isinstance(results, dict) and "message" in results:
                                        message = results["message"]
                                        logger.info(f"Found message in results: {type(message)}")
                                        
                                        if isinstance(message, dict) and "data" in message:
                                            message_data = message["data"]
                                            logger.info(f"Found message data: {type(message_data)}")
                                            
                                            if isinstance(message_data, dict) and "text" in message_data:
                                                text = message_data["text"]
                                                logger.info(f"Extracted text from nested structure: {text[:100]}...")
                                                return text
                
                # Handle the artifacts.message structure
                if "artifacts" in data:
                    artifacts = data["artifacts"]
                    logger.info(f"Found artifacts: {type(artifacts)}")
                    if isinstance(artifacts, dict) and "message" in artifacts:
                        text = artifacts["message"]
                        logger.info(f"Extracted text from artifacts.message: {text[:100]}...")
                        return text
                
                # Handle the outputs.message.message structure (fallback)
                if "outputs" in data:
                    outputs = data["outputs"]
                    if isinstance(outputs, dict) and "message" in outputs:
                        message = outputs["message"]
                        if isinstance(message, dict) and "message" in message:
                            text = message["message"]
                            logger.info(f"Extracted text from outputs.message.message: {text[:100]}...")
                            return text
                        elif isinstance(message, str):
                            logger.info(f"Extracted text from outputs.message: {message[:100]}...")
                            return message
                
                # Handle messages array structure
                if "messages" in data:
                    messages = data["messages"]
                    logger.info(f"Found messages array: {len(messages) if isinstance(messages, list) else 'not a list'}")
                    if isinstance(messages, list) and len(messages) > 0:
                        first_message = messages[0]
                        if isinstance(first_message, dict) and "message" in first_message:
                            text = first_message["message"]
                            logger.info(f"Extracted text from messages[0].message: {text[:100]}...")
                            return text
                
                # Look for any text content in the response
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 20 and value != "langflow_session":
                        logger.info(f"Found text in key '{key}': {value[:100]}...")
                        return value
                    elif isinstance(value, dict):
                        # Recursively search in nested dictionaries
                        nested_text = self._extract_langflow_text(value)
                        if nested_text and nested_text != "No response generated" and nested_text != "langflow_session":
                            logger.info(f"Found nested text: {nested_text[:100]}...")
                            return nested_text
                
                # Fallback to general text extraction
                logger.info("Using fallback text extraction")
                result = self._extract_text_from_json(data)
                logger.info(f"Fallback result: {result[:100]}...")
                return result
            
            elif isinstance(data, list) and len(data) > 0:
                logger.info("Data is list, processing first item")
                return self._extract_langflow_text(data[0])
            
            logger.warning("No response generated - data structure not recognized")
            return "No response generated"
        except Exception as e:
            logger.error(f"Error extracting Langflow text: {e}")
            return "Error extracting response text"
    
    def _extract_text_from_json(self, data):
        """Extract text content from nested JSON structure"""
        if isinstance(data, dict):
            # Look for common text fields
            for key in ['text', 'response', 'output', 'message', 'content', 'result', 'data']:
                if key in data:
                    value = data[key]
                    if isinstance(value, str) and value.strip():
                        return value
                    elif isinstance(value, (dict, list)):
                        return self._extract_text_from_json(value)
            
            # If no direct text field, look in nested structures
            for value in data.values():
                if isinstance(value, str) and value.strip() and len(value) > 10:
                    return value
                elif isinstance(value, (dict, list)):
                    result = self._extract_text_from_json(value)
                    if result and result != "No response generated":
                        return result
        
        elif isinstance(data, list) and len(data) > 0:
            # Try to extract from first item in list
            return self._extract_text_from_json(data[0])
        
        return "No response generated"
    
    async def close(self):
        """Close the client and cleanup resources"""
        await self._close_session()
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the Direct Langflow Client"""
        return {
            "name": "Direct Langflow Client",
            "description": "Direct API integration with Langflow (no MCP)",
            "host_url": self.host_url,
            "flow_id": self.flow_id,
            "capabilities": [
                "Direct chat with Langflow flows",
                "Direct flow execution",
                "Session management",
                "Flow discovery",
                "Health monitoring"
            ],
            "endpoints": {
                "health": f"{self.host_url}/api/v1/health",
                "flows": f"{self.host_url}/api/v1/flows",
                "run_flow": f"{self.host_url}/api/v1/run/{self.flow_id}",
                "flow_info": f"{self.host_url}/api/v1/flows/{self.flow_id}"
            },
            "method": "direct_api"
        }
