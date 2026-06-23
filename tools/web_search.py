from ddgs import DDGS
from typing import Optional


def get_system_schema():
    """Tool definition – kept for compatibility with function‑calling models."""
    return {
        "name": "get_web_search_summaries",
        "description": "Call whenever real‑time data, weather, dates, news or live lookups are needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Specific query keywords."}
            },
            "required": ["query"],
        },
    }


def execute_tool_sync(query: str) -> Optional[str]:
    """
    Fetch a useful answer for the given query using DDGS.
    - First tries the instant‑answer API (for weather, calculations, etc.)
    - If that fails, performs a text search and returns up to 3 snippets.
    - If still empty, tries a simplified query (removes date‑specific words).
    Returns `None` only if absolutely nothing can be found.
    """
    try:
        with DDGS() as ddgs:
            try:
                instant = list(ddgs.answers(query))
                if instant and instant[0].get("text"):
                    answer = instant[0]["text"].strip()
                    if answer:
                        return f"[Direct Answer]\n{answer}"
            except Exception:
                pass

            results = list(ddgs.text(query, max_results=3))
            if results:
                cleaned = []
                for i, res in enumerate(results, start=1):
                    body = res.get("body", "").strip()
                    if body:
                        cleaned.append(f"[{i}] {body}")
                if cleaned:
                    return "\n\n".join(cleaned)


            import re
            simple = re.sub(r'\b(yesterday|today|now|currently|tonight|night)\b', '', query, flags=re.IGNORECASE)
            simple = re.sub(r'\s+', ' ', simple).strip()
            if simple and simple != query:
                print(f"[SEARCH] Retrying with simplified query: '{simple}'")
                fallback_results = list(ddgs.text(simple, max_results=3))
                if fallback_results:
                    cleaned = []
                    for i, res in enumerate(fallback_results, start=1):
                        body = res.get("body", "").strip()
                        if body:
                            cleaned.append(f"[{i}] {body}")
                    if cleaned:
                        return "\n\n".join(cleaned)

            return None

    except Exception as e:
        print(f"[SEARCH ERROR] {e}")
        return None