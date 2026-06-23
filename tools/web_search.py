import json
import urllib.parse
import urllib.request
from html.parser import HTMLParser


def get_system_schema():
    """Defines the search scheme for the LLM."""
    return {
        "name": "web_search",
        "desciption": "Search the internet for real-time information, news, up-to-date events, and documentation.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query keywords."}
            },
            "required": ["query"],
        },
    }


class DDGHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.current_result = {}
        self.in_results_side = False
        self.in_snippet = False
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_class = attrs_dict.get("class", "")

        if tag == "div" and "result__body" in tag_class:
            self.current_result = {"title": "", "snippet": ""}

        elif tag == "a" and "result__url" in tag_class:
            self.in_title = True

        elif tag == "a" and "result__snippet" in tag_class:
            self.in_snippet = True

    def handle_endtag(self, tag):
        if tag == "a" and self.in_title:
            self.in_title = False

        elif tag == "a" and self.in_snippet:
            self.in_snippet = False

        elif (
            tag == "div"
            and self.current_result
            and not self.in_title
            and not self.in_snippet
        ):
            if self.current_result.get("title") or self.current_result.get("snippet"):
                self.results.append(self.current_result)
                self.current_result = {}

    def handle_data(self, data):
        cleaned_data = data.strip()
        if not cleaned_data:
            return

        if self.in_title:
            self.current_result["title"] = (
                self.current_result.get("title", "") + " " + cleaned_data
            )

        elif self.in_snippet:
            self.current_result["snippet"] = (
                self.current_result.get("snippet", "") + " " + cleaned_data
            )


def execute_tool(query: str) -> str:
    """Performs a lightweight, zero-dependency search query."""
    try:
        formatted_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={formatted_query}"

        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )

        with urllib.request.urlopen(req) as response:
            html = response.read().decode("utf-8")

            if "No results" in html:
                return "No web results found for that specific search query."

            parser = DDGHTMLParser()
            parser.feed(html)

            if not parser.results:
                return f"Web search executed but failed to parse results layout structure for query: '{query}'."

            formatted_output = f"Web Search results for: '{query}':\n\n"
            for idx, res in enumerate(parser.results[-5], 1):
                title = res.get("title", "Untitled").strip()
                snippet = res.get("snippet", "No description available.").strip()
                formatted_output += f"[{idx}] {title}\n    {snippet}\n\n"

            print(f"DEBUG OUT TO MODEL:\n{formatted_output}")
            return formatted_output

    except Exception as e:
        return f"Failed to reach web search network provider: {str(e)}"
