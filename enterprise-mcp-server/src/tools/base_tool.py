"""
Enterprise Tool Architecture
SOLID Principle: Open/Closed - Zero-configuration auto-discovery of tools
Enterprise Standard: Single source of truth for all tool management
"""

import inspect
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass


@dataclass
class EnterpriseToolMetadata:
    """Enterprise tool metadata with full auto-discovery"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str
    return_type: str


class EnterpriseToolRegistry:
    """Enterprise registry with zero-configuration auto-discovery"""
    
    _tools: Dict[str, EnterpriseToolMetadata] = {}
    _categories: Dict[str, List[str]] = {}
    
    @classmethod
    def auto_register_tool(
        cls,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general"
    ):
        """Enterprise decorator for zero-configuration auto-discovery"""
        def decorator(func: Callable) -> Callable:
            # Auto-generate name from function name
            tool_name = name or func.__name__
            
            # Auto-generate description from docstring
            tool_description = description or func.__doc__ or f"Tool: {tool_name}"
            
            # Auto-discover parameters from function signature
            sig = inspect.signature(func)
            auto_parameters = {}
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':  # Skip self parameter
                    continue
                
                # Get type annotation
                param_type = param.annotation
                if param_type == inspect.Parameter.empty:
                    param_type = str
                
                # Convert type to string representation
                if hasattr(param_type, '__name__'):
                    type_name = param_type.__name__
                else:
                    type_name = str(param_type)
                
                param_info = {
                    "type": type_name,
                    "description": f"Parameter {param_name}",
                    "required": param.default == inspect.Parameter.empty
                }
                
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                
                auto_parameters[param_name] = param_info
            
            # Auto-discover return type
            return_type = "string"  # Default
            if hasattr(func, '__annotations__') and 'return' in func.__annotations__:
                return_annotation = func.__annotations__['return']
                if hasattr(return_annotation, '__name__'):
                    return_type = return_annotation.__name__
            
            # Register tool
            tool_metadata = EnterpriseToolMetadata(
                name=tool_name,
                description=tool_description,
                parameters=auto_parameters,
                category=category,
                return_type=return_type
            )
            
            cls._tools[tool_name] = tool_metadata
            
            # Add to category
            if category not in cls._categories:
                cls._categories[category] = []
            cls._categories[category].append(tool_name)
            
            # Store metadata on function
            func._tool_metadata = tool_metadata
            func._is_tool = True
            
            return func
        
        return decorator
    
    @classmethod
    def get_tools_metadata(cls, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tools metadata with full auto-discovery"""
        if category:
            tool_names = cls._categories.get(category, [])
            return [
                {
                    "name": cls._tools[name].name,
                    "description": cls._tools[name].description,
                    "parameters": cls._tools[name].parameters,
                    "return_type": cls._tools[name].return_type
                }
                for name in tool_names
            ]
        else:
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "return_type": tool.return_type
                }
                for tool in cls._tools.values()
            ]
    
    @classmethod
    def get_categories(cls) -> Dict[str, List[str]]:
        """Get all categories and their tools"""
        return cls._categories.copy()
    
    @classmethod
    def get_tool_by_name(cls, name: str) -> Optional[EnterpriseToolMetadata]:
        """Get specific tool metadata"""
        return cls._tools.get(name)


def enterprise_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general"
):
    """Enterprise decorator for zero-configuration auto-discovery"""
    return EnterpriseToolRegistry.auto_register_tool(name, description, category)
