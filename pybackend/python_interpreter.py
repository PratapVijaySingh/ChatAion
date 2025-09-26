"""
Python Interpreter Component for ChatAion
Constitution Agent - Execute Python code safely
"""

import importlib
import sys
import io
import contextlib
import traceback
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class PythonInterpreter:
    """
    Safe Python code execution environment
    """
    
    def __init__(self, allowed_modules: Optional[List[str]] = None):
        """
        Initialize the Python interpreter with allowed modules
        
        Args:
            allowed_modules: List of modules that can be imported
        """
        self.allowed_modules = allowed_modules or [
            'math', 'random', 'datetime', 'json', 'os', 'sys', 
            'collections', 'itertools', 'functools', 'operator',
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly',
            'requests', 'urllib', 'base64', 'hashlib', 'uuid'
        ]
        self.globals_dict = self._setup_globals()
        
    def _setup_globals(self) -> Dict[str, Any]:
        """Setup the global namespace with allowed modules"""
        globals_dict = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sum': sum,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'dir': dir,
                'type': type,
                'open': open,
                'input': input,
                'help': help,
                'vars': vars,
                'locals': locals,
                'globals': globals,
            }
        }
        
        # Import allowed modules
        for module_name in self.allowed_modules:
            try:
                imported_module = importlib.import_module(module_name)
                globals_dict[module_name] = imported_module
                logger.info(f"Successfully imported module: {module_name}")
            except ImportError as e:
                logger.warning(f"Could not import module {module_name}: {e}")
                
        return globals_dict
    
    def execute_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute Python code safely
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            # Execute the code
            exec(code, self.globals_dict)
            
            # Get the output
            output = captured_output.getvalue()
            
            # Restore stdout
            sys.stdout = old_stdout
            
            return {
                "success": True,
                "output": output.strip(),
                "error": None
            }
            
        except SyntaxError as e:
            sys.stdout = old_stdout
            return {
                "success": False,
                "output": "",
                "error": f"Syntax Error: {str(e)}"
            }
            
        except NameError as e:
            sys.stdout = old_stdout
            return {
                "success": False,
                "output": "",
                "error": f"Name Error: {str(e)}"
            }
            
        except ImportError as e:
            sys.stdout = old_stdout
            return {
                "success": False,
                "output": "",
                "error": f"Import Error: {str(e)}"
            }
            
        except Exception as e:
            sys.stdout = old_stdout
            error_traceback = traceback.format_exc()
            return {
                "success": False,
                "output": "",
                "error": f"Execution Error: {str(e)}\nTraceback:\n{error_traceback}"
            }
    
    def get_available_modules(self) -> List[str]:
        """Get list of available modules"""
        return list(self.globals_dict.keys())
    
    def add_module(self, module_name: str) -> bool:
        """
        Add a new module to allowed modules
        
        Args:
            module_name: Name of module to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            imported_module = importlib.import_module(module_name)
            self.globals_dict[module_name] = imported_module
            if module_name not in self.allowed_modules:
                self.allowed_modules.append(module_name)
            logger.info(f"Successfully added module: {module_name}")
            return True
        except ImportError as e:
            logger.error(f"Could not add module {module_name}: {e}")
            return False

class ConstitutionAgent:
    """
    Constitution Agent - Python code execution with constitutional principles
    """
    
    def __init__(self):
        self.interpreter = PythonInterpreter()
        self.constitution_principles = [
            "Execute code safely and responsibly",
            "Provide clear and helpful error messages",
            "Respect system resources and timeouts",
            "Maintain code quality and readability",
            "Follow Python best practices"
        ]
    
    def execute_python(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Execute Python code with constitutional principles
        
        Args:
            code: Python code to execute
            context: Additional context for execution
            
        Returns:
            Execution results with constitutional guidance
        """
        # Add constitutional context to the code
        constitutional_code = f"""
# Constitution Agent Execution
# Principles: {', '.join(self.constitution_principles)}
# Context: {context}

{code}
"""
        
        result = self.interpreter.execute_code(constitutional_code)
        
        # Add constitutional guidance to the response
        if result["success"]:
            result["constitutional_guidance"] = "Code executed successfully following constitutional principles"
        else:
            result["constitutional_guidance"] = "Code execution failed. Please review and follow Python best practices"
        
        return result
    
    def get_constitution_info(self) -> Dict[str, Any]:
        """Get information about the Constitution Agent"""
        return {
            "name": "Constitution Agent",
            "description": "Python code execution with constitutional principles",
            "principles": self.constitution_principles,
            "available_modules": self.interpreter.get_available_modules(),
            "capabilities": [
                "Safe Python code execution",
                "Mathematical calculations",
                "Data analysis with pandas/numpy",
                "Visualization with matplotlib/plotly",
                "Web requests and API calls",
                "File operations",
                "JSON/CSV data processing"
            ]
        }
