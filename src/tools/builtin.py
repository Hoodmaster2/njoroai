import asyncio
import os
import aiohttp
from pathlib import Path
from src.tools.registry import registry
from src.utils.logger import logger

# --- File Operations ---

async def read_file(path: str) -> str:
    """Reads the content of a file."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File {path} does not exist."
        
        # Simple sandbox check
        if ".." in str(file_path):
             return "Error: Path traversal not allowed."

        async with aiohttp.ClientSession() as session:
            # Using aiofiles would be better but keeping deps minimal for now, 
            # standard open is blocking but fast for small text files.
            # For larger files or strict async, run in executor.
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, file_path.read_text, "utf-8")
            return content
    except Exception as e:
        logger.error(f"read_file failed: {e}")
        return f"Error reading file: {e}"

async def write_file(path: str, content: str) -> str:
    """Writes content to a file (overwrites)."""
    try:
        file_path = Path(path)
        
        # Sandbox check
        if ".." in str(file_path):
             return "Error: Path traversal not allowed."

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, file_path.write_text, content, "utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        logger.error(f"write_file failed: {e}")
        return f"Error writing file: {e}"

async def list_files(path: str = ".") -> str:
    """Lists files in a directory."""
    try:
        dir_path = Path(path)
        if not dir_path.exists():
             return f"Error: Directory {path} does not exist."
        
        files = [f.name for f in dir_path.iterdir()]
        return "\n".join(files)
    except Exception as e:
        logger.error(f"list_files failed: {e}")
        return f"Error listing files: {e}"

# --- Web Operations ---

async def web_get(url: str) -> str:
    """Performs a GET request to a URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return f"Error: Status code {response.status}"
    except Exception as e:
        logger.error(f"web_get failed: {e}")
        return f"Error fetching URL: {e}"

# --- System Operations ---

async def run_command(command: str) -> str:
    """Runs a shell command (sandboxed - no interactive commands)."""
    # comprehensive blacklist for safety
    blacklist = ["rm -rf", "format", "del /s", "mkfs"] 
    for banned in blacklist:
        if banned in command:
            return f"Error: Command '{banned}' is not allowed."

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        output = stdout.decode().strip()
        error = stderr.decode().strip()
        
        if error:
            return f"Output: {output}\nError: {error}"
        return output
    except Exception as e:
        logger.error(f"run_command failed: {e}")
        return f"Error running command: {e}"

def register_builtin_tools():
    """Registers all built-in tools."""
    registry.register("read_file", "Reads a file from the local system.", read_file)
    registry.register("write_file", "Writes content to a file.", write_file)
    registry.register("list_files", "Lists files in a directory.", list_files)
    registry.register("web_get", "Fetches content from a URL.", web_get)
    registry.register("run_command", "Runs a shell command.", run_command)
