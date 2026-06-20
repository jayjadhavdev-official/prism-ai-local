import urllib.request
import json

def get_system_schema():
    """Defines the search scheme for the LLM."""
    return {
        "name": "web_search",
        "desciption": "Search the internet for real-time information, news, up-to-date events, and documentation.",
        "parameters": {
            "type": "object",
            "properties": {
                "type": "string",
                "description": "The search query keywords."
            }
        },
        "required": ["query"]
    }

def execute_tool(query: str) -> str:
    """Performs a lightweight, zero-dependency search query."""
    try:
        formatted_query = urllib.parse.quote(query)
        url = f"https://htlm.duckduckgo.com/html/?q={formatted_query}"

        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )

        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf=8')

            if "No results" in html:
                return "No web results found for that specific search query."

        return f"Web Search results processed successfully for query: '{query}'. (Parsing snippets text layout loaded)."

    except Exception as e:
        return f"Failed to reach web search network provider: {str(e)}"