import json
import asyncio
import sys

def get_system_schema():
    """Defines the search schema for the LLM."""
    return {
        "name": "web_search",
        "description": "Search the internet for real-time information, weather, news, and live updates.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query keywords."}
            },
            "required": ["query"],
        },
    }

async def execute_tool_async(query: str) -> str:
    """
    Asynchronously invokes the web-search-mcp server via stdio,
    dispatches the JSON-RPC payload, and reads back the clean snippets.
    """
    try:
        # Launch the local MCP server via npx
        process = await asyncio.create_subprocess_exec(
            "npx", "-y", "websearch-mcp",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

        # Build standardized MCP JSON-RPC payload
        # Using get-web-search-summaries for lightweight result text snippets
        mcp_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "get-web-search-summaries",
                "arguments": {
                    "query": query,
                    "limit": 3
                }
            }
        }

        input_data = json.dumps(mcp_payload) + "\n"
        stdout, _ = await process.communicate(input=input_data.encode("utf-8"))

        response_data = json.loads(stdout.decode("utf-8"))
        content_items = response_data.get("result", {}).get("content", [])
        
        if content_items:
            return content_items[0].get("text", "No context returned from browser execution.")
        
        return "Local search node returned an empty text canvas context."

    except Exception as e:
        return f"Local web-search-mcp bridge failed: {str(e)}"

def execute_tool(query: str) -> str:
    """Synchronous entry point that safely wraps the async subprocess logic."""
    try:
        # Run the async loop inside our synchronous backend framework wrapper
        return asyncio.run(execute_tool_async(query))
    except Exception as e:
        return f"Async wrapper error inside web_search execution block: {str(e)}"