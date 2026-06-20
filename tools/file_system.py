import os
from pathlib import Path

def get_system_schema():
    """Defines the tool structure for the LLM."""
    return {
        "name": "explore_directory",
        "description": "List all files and folders in a given target directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The target directory path. Use '~' to target the user's home directory across any operating system."
                }
            },
            "required": ["path"]
        }
    }

def execute_tool(path: str) -> str:
    """Safely reads directory contents across platforms."""
    try:
        target_path = Path(path).expanduser().resolve()

        if not target_path.exists():
            return f"Error: The path '{path}' does not exist on this machine."

        if not target_path.is_dir():
            return f"Error: '{path}' is a file, not a directory."

        items = os.listdir(target_path)
        folders = [f + "/" for f in items if (target_path / f).is_dir()]
        files = [f for f in items if (target_path / f).is_file()]

        output = f"Contents of {target_path}:\n"
        output += f"Directories: {','.join(folders) if folders else 'None'}\n"
        output += f"Files: {','.join(files) if files else 'None'}"
        return output

    except Exception as e:
        return f"Permission denied or access error: {str(e)}"