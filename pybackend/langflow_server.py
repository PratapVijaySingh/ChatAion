#!/usr/bin/env python3
"""
Langflow Agent MCP Server
Advanced AI workflows through Langflow integration
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, List, Optional
from langflow_agent import LangflowAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangflowMCPServer:
    """MCP Server for Langflow Agent"""
    
    def __init__(self):
        self.agent = LangflowAgent()
        self.server_info = {
            "name": "Langflow Agent",
            "version": "1.0.0",
            "description": "Advanced AI workflows through Langflow integration"
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "initialize":
                return await self.initialize(params)
            elif method == "tools/list":
                return await self.list_tools()
            elif method == "tools/call":
                return await self.call_tool(params)
            elif method == "langflow/health":
                return await self.check_health()
            elif method == "langflow/flows":
                return await self.get_flows()
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the MCP server"""
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": self.server_info
            }
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "result": {
                "tools": [
                    {
                        "name": "chat_with_langflow",
                        "description": "Chat with Langflow AI workflows",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Message to send to Langflow"
                                },
                                "session_id": {
                                    "type": "string",
                                    "description": "Optional session ID for conversation continuity",
                                    "default": ""
                                }
                            },
                            "required": ["message"]
                        }
                    },
                    {
                        "name": "run_flow",
                        "description": "Run a Langflow flow with custom inputs",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "inputs": {
                                    "type": "object",
                                    "description": "Input data for the flow"
                                },
                                "session_id": {
                                    "type": "string",
                                    "description": "Optional session ID",
                                    "default": ""
                                }
                            },
                            "required": ["inputs"]
                        }
                    },
                    {
                        "name": "check_connection",
                        "description": "Check Langflow server connection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_flow_info",
                        "description": "Get information about the current flow",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_flow_schema",
                        "description": "Get the schema/inputs for the current flow",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_available_flows",
                        "description": "Get list of available flows from Langflow server",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }
    
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "chat_with_langflow":
                message = arguments.get("message", "")
                session_id = arguments.get("session_id", "")
                
                if not message.strip():
                    return {
                        "error": {
                            "code": -32602,
                            "message": "Message is required"
                        }
                    }
                
                result = await self.agent.chat_with_flow(message, session_id)
                
                if result["success"]:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Langflow Response:**\n\n{result['response']}\n\n**Session ID:** {result['session_id']}\n**Execution Time:** {result['execution_time']}s"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Error:** {result['error']}"
                                }
                            ]
                        }
                    }
                    
            elif tool_name == "run_flow":
                inputs = arguments.get("inputs", {})
                session_id = arguments.get("session_id", "")
                
                result = await self.agent.run_flow(inputs, session_id)
                
                if result["success"]:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Flow Execution Result:**\n\n```json\n{json.dumps(result['outputs'], indent=2)}\n```\n\n**Session ID:** {result['session_id']}\n**Execution Time:** {result['execution_time']}s"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Error:** {result['error']}"
                                }
                            ]
                        }
                    }
                    
            elif tool_name == "check_connection":
                result = await self.agent.check_connection()
                
                if result["success"]:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Connection Status:** ✅ Connected\n**Host:** {result['host_url']}\n**Server Info:** {json.dumps(result.get('server_info', {}), indent=2)}"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Connection Status:** ❌ Failed\n**Host:** {result['host_url']}\n**Error:** {result['error']}"
                                }
                            ]
                        }
                    }
                    
            elif tool_name == "get_flow_info":
                result = await self.agent.get_flow_info()
                
                if result["success"]:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Flow Information:**\n\n```json\n{json.dumps(result['flow_info'], indent=2)}\n```"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Error:** {result['error']}"
                                }
                            ]
                        }
                    }
                    
            elif tool_name == "get_flow_schema":
                result = await self.agent.get_flow_schema()
                
                if result["success"]:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Flow Schema:**\n\n```json\n{json.dumps(result['schema'], indent=2)}\n```"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Error:** {result['error']}"
                                }
                            ]
                        }
                    }
                    
            elif tool_name == "get_available_flows":
                result = await self.agent.get_available_flows()
                
                if result["success"]:
                    flows_info = result['flows']
                    flows_text = "\n".join([f"- {flow.get('name', 'Unknown')} (ID: {flow.get('id', 'Unknown')})" for flow in flows_info[:10]])
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Available Flows ({result['count']}):**\n\n{flows_text}\n\n*Showing first 10 flows*"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**Error:** {result['error']}"
                                }
                            ]
                        }
                    }
                    
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    async def check_health(self) -> Dict[str, Any]:
        """Check Langflow server health"""
        result = await self.agent.check_connection()
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"**Health Check:** {'✅ Healthy' if result['success'] else '❌ Unhealthy'}\n**Host:** {result['host_url']}"
                    }
                ]
            }
        }
    
    async def get_flows(self) -> Dict[str, Any]:
        """Get available flows"""
        result = await self.agent.get_available_flows()
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"**Available Flows:** {result['count'] if result['success'] else 'Error: ' + result['error']}"
                    }
                ]
            }
        }

async def main():
    """Main server loop"""
    server = LangflowMCPServer()
    
    logger.info("Langflow Agent MCP Server starting...")
    
    try:
        while True:
            # Read request from stdin
            line = sys.stdin.readline()
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                
                # Send response to stdout
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await server.agent.close()

if __name__ == "__main__":
    asyncio.run(main())
