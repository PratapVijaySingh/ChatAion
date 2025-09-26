#!/usr/bin/env python3
"""
Constitution Agent MCP Server
Python code execution with constitutional principles
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, List, Optional
from python_interpreter import ConstitutionAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstitutionMCPServer:
    """MCP Server for Constitution Agent"""
    
    def __init__(self):
        self.agent = ConstitutionAgent()
        self.server_info = {
            "name": "Constitution Agent",
            "version": "1.0.0",
            "description": "Python code execution with constitutional principles"
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
            elif method == "constitution/info":
                return await self.get_constitution_info()
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
                        "name": "execute_python",
                        "description": "Execute Python code safely with constitutional principles",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Python code to execute"
                                },
                                "context": {
                                    "type": "string", 
                                    "description": "Additional context for execution",
                                    "default": ""
                                }
                            },
                            "required": ["code"]
                        }
                    },
                    {
                        "name": "get_available_modules",
                        "description": "Get list of available Python modules",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "add_module",
                        "description": "Add a new module to allowed modules",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "module_name": {
                                    "type": "string",
                                    "description": "Name of module to add"
                                }
                            },
                            "required": ["module_name"]
                        }
                    },
                    {
                        "name": "get_constitution_info",
                        "description": "Get information about constitutional principles",
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
            if tool_name == "execute_python":
                code = arguments.get("code", "")
                context = arguments.get("context", "")
                result = self.agent.execute_python(code, context)
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**Execution Result:**\n\n```python\n{code}\n```\n\n**Output:**\n```\n{result.get('output', '')}\n```\n\n**Status:** {'✅ Success' if result.get('success') else '❌ Error'}\n\n**Constitutional Guidance:** {result.get('constitutional_guidance', '')}"
                            }
                        ]
                    }
                }
                
            elif tool_name == "get_available_modules":
                modules = self.agent.interpreter.get_available_modules()
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**Available Modules:**\n\n{', '.join(modules)}"
                            }
                        ]
                    }
                }
                
            elif tool_name == "add_module":
                module_name = arguments.get("module_name", "")
                success = self.agent.interpreter.add_module(module_name)
                status = "✅ Successfully added" if success else "❌ Failed to add"
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**Add Module Result:**\n\nModule: `{module_name}`\nStatus: {status}"
                            }
                        ]
                    }
                }
                
            elif tool_name == "get_constitution_info":
                info = self.agent.get_constitution_info()
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**Constitution Agent Information:**\n\n**Name:** {info['name']}\n**Description:** {info['description']}\n\n**Constitutional Principles:**\n" + 
                                       "\n".join([f"• {principle}" for principle in info['principles']]) +
                                       f"\n\n**Capabilities:**\n" + 
                                       "\n".join([f"• {capability}" for capability in info['capabilities']]) +
                                       f"\n\n**Available Modules:** {', '.join(info['available_modules'])}"
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

async def main():
    """Main server loop"""
    server = ConstitutionMCPServer()
    
    logger.info("Constitution Agent MCP Server starting...")
    
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

if __name__ == "__main__":
    asyncio.run(main())
