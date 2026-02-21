import inspect
import asyncio
from typing import Callable, Dict, Any, Optional
from src.utils.logger import logger
from src.persistence.database import db

class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}

    def register(self, name: str, description: str, func: Callable):
        """Register a tool with the system."""
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Tool {name} must be an async function.")
            
        self._tools[name] = func
        self._descriptions[name] = description
        
        # Ensure tool exists in DB
        try:
            existing = db.fetch_one("SELECT * FROM tools WHERE name = ?", (name,))
            if not existing:
                db.execute_query(
                    "INSERT INTO tools (name, description, code, enabled) VALUES (?, ?, ?, ?)",
                    (name, description, inspect.getsource(func), True)
                )
            else:
                # Update description/code if changed (optional, but good for sync)
                pass
        except Exception as e:
            logger.error(f"Failed to register tool {name} in DB: {e}")

    def get_tool(self, name: str) -> Optional[Callable]:
        """Retrieve a tool if it exists and is enabled."""
        try:
            row = db.fetch_one("SELECT enabled FROM tools WHERE name = ?", (name,))
            if row and row['enabled']:
                return self._tools.get(name)
            elif row and not row['enabled']:
                logger.warning(f"Tool {name} is disabled.")
                return None
            else:
                logger.warning(f"Tool {name} not found in DB.")
                return None
        except Exception as e:
            logger.error(f"Error checking tool status: {e}")
            return None

    def get_all_tools(self) -> Dict[str, str]:
        """Get all registered tools and their descriptions."""
        # Return only enabled tools
        enabled_tools = {}
        try:
            rows = db.fetch_all("SELECT name FROM tools WHERE enabled = 1")
            enabled_names = {row['name'] for row in rows}
            
            for name, desc in self._descriptions.items():
                if name in enabled_names:
                    enabled_tools[name] = desc
        except Exception as e:
            logger.error(f"Error fetching enabled tools: {e}")
            # Fallback to in-memory if DB fails
            return self._descriptions
            
        return enabled_tools

    async def execute(self, name: str, **kwargs) -> Any:
        """Execute a tool safely."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool {name} is not available.")
            
        try:
            logger.info(f"Executing tool: {name} with args: {kwargs}")
            return await tool(**kwargs)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise

# Global registry instance
registry = ToolRegistry()
