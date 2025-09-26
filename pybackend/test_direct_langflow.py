#!/usr/bin/env python3
"""
Test script for Direct Langflow functionality
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_direct_langflow():
    """Test the Direct Langflow functionality"""
    try:
        from direct_langflow import DirectLangflowClient
        print("✅ Direct Langflow Client imported successfully")
        
        # Create client instance
        client = DirectLangflowClient()
        print("✅ Direct Langflow Client initialized")
        
        # Test connection check
        print("🔍 Testing direct connection to Langflow server...")
        connection_result = await client.check_connection()
        print(f"Connection test: {'✅ Success' if connection_result['success'] else '❌ Failed'}")
        if not connection_result['success']:
            print(f"Error: {connection_result['error']}")
            print("Note: Make sure Langflow server is running on http://localhost:7860")
        else:
            print(f"Host: {connection_result['host_url']}")
            print(f"Status: {connection_result['status']}")
        
        # Test client info
        info = client.get_client_info()
        print(f"✅ Client info: {info['name']}")
        print(f"Host URL: {info['host_url']}")
        print(f"Flow ID: {info['flow_id']}")
        print(f"Method: {info['method']}")
        
        # Test available flows (if connection is successful)
        if connection_result['success']:
            print("🔍 Testing available flows...")
            flows_result = await client.get_available_flows_direct()
            print(f"Flows test: {'✅ Success' if flows_result['success'] else '❌ Failed'}")
            if flows_result['success']:
                print(f"Available flows: {flows_result['count']}")
            
            # Test flow info
            print("🔍 Testing flow info...")
            flow_info_result = await client.get_flow_info_direct()
            print(f"Flow info test: {'✅ Success' if flow_info_result['success'] else '❌ Failed'}")
        
        # Test direct chat functionality (if connection is successful)
        if connection_result['success']:
            print("🔍 Testing direct chat functionality...")
            chat_result = await client.chat_direct("Hello, this is a direct test message")
            print(f"Direct chat test: {'✅ Success' if chat_result['success'] else '❌ Failed'}")
            if chat_result['success']:
                print(f"Response: {chat_result['response'][:100]}...")
                print(f"Session ID: {chat_result['session_id']}")
                print(f"Execution Time: {chat_result['execution_time']}s")
            else:
                print(f"Error: {chat_result['error']}")
        
        # Close client
        await client.close()
        print("✅ Client closed successfully")
        
        print("🎉 All Direct Langflow tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main test function"""
    success = await test_direct_langflow()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
