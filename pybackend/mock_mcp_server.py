#!/usr/bin/env python3
"""
Simple mock MCP server for testing
"""

import asyncio
import json
import sys
import signal
from typing import Any, Dict

class MockMCPServer:
    def __init__(self):
        self.tools = [
            {
                "name": "get_weather",
                "description": "Get weather information for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_time",
                "description": "Get current time",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        request_id = request.get("id", 1)
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mock-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": self.tools
                }
            }
        
        elif method == "tools/call":
            tool_name = request.get("params", {}).get("name")
            arguments = request.get("params", {}).get("arguments", {})
            
            if tool_name == "get_weather":
                location = arguments.get("location", "Unknown")
                result = f"Weather in {location}: Sunny, 72°F"
            elif tool_name == "get_time":
                import datetime
                result = f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                result = f"Unknown tool: {tool_name}"
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def run(self):
        """Run the MCP server"""
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while True:
                try:
                    # Read line from stdin
                    line = sys.stdin.readline()
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse JSON request
                    request = json.loads(line)
                    
                    # Handle the request
                    response = await self.handle_request(request)
                    
                    # Send response
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    # Send error response for invalid JSON
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    continue
                    
                except Exception as e:
                    # Send error response for other errors
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    continue
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            # Final error response
            error_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32603,
                    "message": f"Server error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    server = MockMCPServer()
    asyncio.run(server.run())
