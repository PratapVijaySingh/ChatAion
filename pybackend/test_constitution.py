#!/usr/bin/env python3
"""
Test script for Constitution Agent functionality
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_constitution_agent():
    """Test the Constitution Agent functionality"""
    try:
        from python_interpreter import ConstitutionAgent
        print("✅ Constitution Agent imported successfully")
        
        # Create agent instance
        agent = ConstitutionAgent()
        print("✅ Constitution Agent initialized")
        
        # Test basic Python execution
        test_code = """
print("Hello from Constitution Agent!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
        
        result = agent.execute_python(test_code, "Basic arithmetic test")
        print(f"✅ Code execution test: {'Success' if result['success'] else 'Failed'}")
        print(f"Output: {result['output']}")
        
        # Test error handling
        error_code = "print(undefined_variable)"
        error_result = agent.execute_python(error_code, "Error handling test")
        print(f"✅ Error handling test: {'Success' if not error_result['success'] else 'Failed'}")
        
        # Test available modules
        modules = agent.interpreter.get_available_modules()
        print(f"✅ Available modules: {len(modules)} modules")
        
        # Test constitution info
        info = agent.get_constitution_info()
        print(f"✅ Constitution info: {info['name']}")
        
        print("🎉 All Constitution Agent tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_constitution_agent()
    sys.exit(0 if success else 1)
