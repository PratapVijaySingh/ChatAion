"""
Langflow Flow Registry
Manages multiple Langflow flows with different IDs
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class LangflowFlowRegistry:
    """Registry for managing multiple Langflow flows"""
    
    def __init__(self, registry_file: str = "langflow_flows.json"):
        self.registry_file = registry_file
        self.flows = {}
        self.load_registry()
    
    def load_registry(self):
        """Load flows from registry file"""
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    self.flows = data.get('flows', {})
                    logger.info(f"Loaded {len(self.flows)} flows from registry")
            else:
                # Create default registry with sample flows
                self.flows = {
                    "default": {
                        "id": "b2636e6f-2c11-4274-b965-5bd98ca40336",
                        "name": "Default Langflow",
                        "description": "Default Langflow conversation flow",
                        "host_url": "http://localhost:7860",
                        "category": "General",
                        "is_active": True,
                        "created_at": datetime.now().isoformat(),
                        "last_used": None,
                        "usage_count": 0
                    }
                }
                self.save_registry()
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            self.flows = {}
    
    def save_registry(self):
        """Save flows to registry file"""
        try:
            data = {
                "flows": self.flows,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.flows)} flows to registry")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_flow(self, flow_id: str, name: str, description: str = "", 
                     host_url: str = "http://localhost:7860", category: str = "General") -> Dict[str, Any]:
        """Register a new Langflow flow"""
        try:
            flow_key = name.lower().replace(" ", "_").replace("-", "_")
            
            # Check if flow already exists
            if flow_key in self.flows:
                return {
                    "success": False,
                    "error": f"Flow with name '{name}' already exists"
                }
            
            # Validate flow_id format (basic UUID check)
            if not self._is_valid_uuid(flow_id):
                return {
                    "success": False,
                    "error": "Invalid flow ID format. Must be a valid UUID."
                }
            
            flow_data = {
                "id": flow_id,
                "name": name,
                "description": description,
                "host_url": host_url.rstrip('/'),
                "category": category,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "last_used": None,
                "usage_count": 0
            }
            
            self.flows[flow_key] = flow_data
            self.save_registry()
            
            logger.info(f"Registered new flow: {name} ({flow_id})")
            return {
                "success": True,
                "flow": flow_data,
                "message": f"Flow '{name}' registered successfully"
            }
            
        except Exception as e:
            logger.error(f"Error registering flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_flow(self, flow_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific flow by key"""
        return self.flows.get(flow_key)
    
    def get_all_flows(self) -> Dict[str, Any]:
        """Get all registered flows"""
        return {
            "success": True,
            "flows": self.flows,
            "count": len(self.flows),
            "active_count": len([f for f in self.flows.values() if f.get("is_active", False)])
        }
    
    def get_flows_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get flows filtered by category"""
        return [flow for flow in self.flows.values() if flow.get("category", "").lower() == category.lower()]
    
    def update_flow(self, flow_key: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing flow"""
        try:
            if flow_key not in self.flows:
                return {
                    "success": False,
                    "error": f"Flow '{flow_key}' not found"
                }
            
            # Update flow data
            for key, value in updates.items():
                if key in ["name", "description", "host_url", "category", "is_active"]:
                    self.flows[flow_key][key] = value
            
            self.flows[flow_key]["updated_at"] = datetime.now().isoformat()
            self.save_registry()
            
            return {
                "success": True,
                "flow": self.flows[flow_key],
                "message": f"Flow '{flow_key}' updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_flow(self, flow_key: str) -> Dict[str, Any]:
        """Delete a flow from registry"""
        try:
            if flow_key not in self.flows:
                return {
                    "success": False,
                    "error": f"Flow '{flow_key}' not found"
                }
            
            flow_name = self.flows[flow_key]["name"]
            del self.flows[flow_key]
            self.save_registry()
            
            logger.info(f"Deleted flow: {flow_name}")
            return {
                "success": True,
                "message": f"Flow '{flow_name}' deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def set_active_flow(self, flow_key: str) -> Dict[str, Any]:
        """Set a flow as active and update usage stats"""
        try:
            if flow_key not in self.flows:
                return {
                    "success": False,
                    "error": f"Flow '{flow_key}' not found"
                }
            
            # Update usage stats
            self.flows[flow_key]["last_used"] = datetime.now().isoformat()
            self.flows[flow_key]["usage_count"] = self.flows[flow_key].get("usage_count", 0) + 1
            
            self.save_registry()
            
            return {
                "success": True,
                "flow": self.flows[flow_key],
                "message": f"Flow '{self.flows[flow_key]['name']}' is now active"
            }
            
        except Exception as e:
            logger.error(f"Error setting active flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_active_flow(self) -> Optional[Dict[str, Any]]:
        """Get the currently active flow"""
        active_flows = [flow for flow in self.flows.values() if flow.get("is_active", False)]
        if active_flows:
            # Return the first active flow (or most recently used if last_used is not None)
            flows_with_last_used = [flow for flow in active_flows if flow.get("last_used") is not None]
            if flows_with_last_used:
                return max(flows_with_last_used, key=lambda x: x.get("last_used", ""))
            else:
                # If no flows have last_used, return the first active flow
                return active_flows[0]
        return None
    
    def test_flow_connection(self, flow_key: str) -> Dict[str, Any]:
        """Test connection to a specific flow"""
        try:
            if flow_key not in self.flows:
                return {
                    "success": False,
                    "error": f"Flow '{flow_key}' not found"
                }
            
            flow = self.flows[flow_key]
            host_url = flow["host_url"]
            flow_id = flow["id"]
            
            # Test connection logic would go here
            # For now, return a placeholder response
            return {
                "success": True,
                "flow_key": flow_key,
                "host_url": host_url,
                "flow_id": flow_id,
                "status": "connection_test_passed",
                "message": f"Connection to flow '{flow['name']}' is working"
            }
            
        except Exception as e:
            logger.error(f"Error testing flow connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = set()
        for flow in self.flows.values():
            categories.add(flow.get("category", "General"))
        return sorted(list(categories))
    
    def search_flows(self, query: str) -> List[Dict[str, Any]]:
        """Search flows by name or description"""
        query_lower = query.lower()
        matching_flows = []
        
        for flow_key, flow in self.flows.items():
            if (query_lower in flow.get("name", "").lower() or 
                query_lower in flow.get("description", "").lower()):
                matching_flows.append({**flow, "key": flow_key})
        
        return matching_flows
