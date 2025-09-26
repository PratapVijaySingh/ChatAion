#!/usr/bin/env python3
"""
Test script for Langflow Agent functionality
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_langflow_agent():
    """Test the Langflow Agent functionality"""
    try:
        from langflow_agent import LangflowAgent
        print("✅ Langflow Agent imported successfully")
        
        # Create agent instance
        agent = LangflowAgent()
        print("✅ Langflow Agent initialized")
        
        # Test connection check
        print("🔍 Testing connection to Langflow server...")
        connection_result = await agent.check_connection()
        print(f"Connection test: {'✅ Success' if connection_result['success'] else '❌ Failed'}")
        if not connection_result['success']:
            print(f"Error: {connection_result['error']}")
            print("Note: Make sure Langflow server is running on http://localhost:7860")
        
        # Test agent info
        info = agent.get_agent_info()
        print(f"✅ Agent info: {info['name']}")
        print(f"Host URL: {info['host_url']}")
        print(f"Flow ID: {info['flow_id']}")
        
        # Test available flows (if connection is successful)
        if connection_result['success']:
            print("🔍 Testing available flows...")
            flows_result = await agent.get_available_flows()
            print(f"Flows test: {'✅ Success' if flows_result['success'] else '❌ Failed'}")
            if flows_result['success']:
                print(f"Available flows: {flows_result['count']}")
            
            # Test flow info
            print("🔍 Testing flow info...")
            flow_info_result = await agent.get_flow_info()
            print(f"Flow info test: {'✅ Success' if flow_info_result['success'] else '❌ Failed'}")
            
            # Test flow schema
            print("🔍 Testing flow schema...")
            schema_result = await agent.get_flow_schema()
            print(f"Flow schema test: {'✅ Success' if schema_result['success'] else '❌ Failed'}")
        
        # Test chat functionality (if connection is successful)
        if connection_result['success']:
            print("🔍 Testing chat functionality...")
            chat_result = await agent.chat_with_flow("Hello, this is a test message")
            print(f"Chat test: {'✅ Success' if chat_result['success'] else '❌ Failed'}")
            if chat_result['success']:
                print(f"Response: {chat_result['response'][:100]}...")
            else:
                print(f"Error: {chat_result['error']}")
        
        # Close agent
        await agent.close()
        print("✅ Agent closed successfully")
        
        print("🎉 All Langflow Agent tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main test function"""
    success = await test_langflow_agent()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
