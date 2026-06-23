import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import ollama  # Native client import

from tools import get_all_tools, call_tool_by_name

app = FastAPI(title="Showcase Local Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tool_call_schema = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["execute_tool", "reply_directly"],
            "description": "Choose whether to call a tool or talk to the user.",
        },
        "tool_name": {
            "type": "string",
            "enum": ["web_search"],
            "description": "The name of the tool to run, if action is execute_tool.",
        },
        "search_query": {
            "type": "string",
            "description": "The target search query string if running a web search.",
        },
        "direct_reply": {
            "type": "string",
            "description": "Your text answer if no web tools are needed.",
        },
    },
    "required": ["action"],
}


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))
        user_message = data.get("message", "hello")
        web_search_active = data.get("webSearchActive", False)

        current_date_str = datetime.now().strftime("%A, %B %d, %Y")

        messages = [
            {
                "role": "system",
                "content": f"You are Prism AI. Current Date: {current_date_str}. Web search tool access: {web_search_active}.",
            },
            {"role": "user", "content": user_message},
        ]

        if web_search_active:
            response = ollama.chat(
                model="gemma4:e2b",
                messages=messages,
                format=tool_call_schema,
                options={"temperature": 0.2} 
            )

            response_json = response.get("message", {}).get("content", "")
            
            if not response_json or not response_json.strip():
                raise ValueError("Ollama native engine returned an empty token response.")
                
            decision = json.loads(response_json.strip())

            if decision.get("action") == "execute_tool":
                function_name = decision.get("tool_name")
                function_args = {"query": decision.get("search_query", "")}

                tool_output = call_tool_by_name(function_name, function_args)

                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Executing local module: {function_name}...",
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": f"System tool feedback loop output:\n{tool_output}",
                    }
                )

                final_stream_response = ollama.chat(
                    model="gemma4:e2b",
                    messages=messages,
                    stream=True,
                )

                def generate_stream():
                    for chunk in final_stream_response:
                        yield chunk.get("message", {}).get("content", "")

                return StreamingResponse(
                    generate_stream(), media_type="text/plain"
                )

            else:
                def generate_static_stream():
                    yield decision.get("direct_reply", "No direct output text returned.")

                return StreamingResponse(
                    generate_static_stream(), media_type="text/plain"
                )

        else:
            direct_stream = ollama.chat(
                model="gemma4:e2b",
                messages=messages,
                stream=True,
            )

            def generate_direct_stream():
                for chunk in direct_stream:
                    yield chunk.get("message", {}).get("content", "")

            return StreamingResponse(
                generate_direct_stream(), media_type="text/plain"
            )

    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)