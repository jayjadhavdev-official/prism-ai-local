import importlib
import os

TOOL_FILES = [f[:-3] for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.py') and f != '__init__.py']

registry = {}
schemas = []

for tool_name in TOOL_FILES:
    module = importlib.import_module(f"tools.{tool_name}")
    if hasattr(module, "get_system_schema") and hasattr(module, "execute_tool"):
        schema = module.get_system_schema()
        registry[schema["name"]] = module.execute_tool
        schemas.append(schema)

def get_all_tools():
    """Returns the JSON definitions the LLM needs to see."""
    return schemas

def call_tool_by_name(name: str, arguments: dict) -> str:
    """Executes the tool function directly matching the call choice of the model."""
    if name in registry:

        if name == "web_search":
            if "queries" in arguments and "query" not in arguments:
                q_val = arguments["queries"]
                arguments["query"] = q_val[0] if isinstance(q_val, list) else q_val
                
        return registry[name](**arguments)
    return f"Tool '{name}' not found in local engine system registry."