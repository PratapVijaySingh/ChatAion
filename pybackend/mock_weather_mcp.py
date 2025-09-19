#!/usr/bin/env python3
"""
Mock Weather MCP Server for testing purposes
"""

import json
import sys
import asyncio
from typing import Any, Dict, List

class MockWeatherMCPServer:
    def __init__(self):
        self.weather_data = {
            "california": {
                "temperature": "72°F",
                "condition": "Sunny",
                "humidity": "45%",
                "wind": "5 mph NW"
            },
            "new york": {
                "temperature": "65°F", 
                "condition": "Partly Cloudy",
                "humidity": "60%",
                "wind": "8 mph SE"
            },
            "london": {
                "temperature": "55°F",
                "condition": "Rainy", 
                "humidity": "80%",
                "wind": "12 mph W"
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "get_weather",
                            "description": "Get current weather for a location",
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
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            if tool_name == "get_weather":
                location = arguments.get("location", "").lower()
                weather = self.weather_data.get(location, {
                    "temperature": "70°F",
                    "condition": "Unknown",
                    "humidity": "50%", 
                    "wind": "5 mph"
                })
                
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Weather in {location.title()}:\n"
                                       f"Temperature: {weather['temperature']}\n"
                                       f"Condition: {weather['condition']}\n"
                                       f"Humidity: {weather['humidity']}\n"
                                       f"Wind: {weather['wind']}"
                            }
                        ]
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }

async def main():
    server = MockWeatherMCPServer()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
