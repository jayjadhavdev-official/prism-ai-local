import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI

from tools import get_all_tools, call_tool_by_name

app = FastAPI(title="Showcase Local Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The structured schema contract for Ollama's grammar constraints
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
        "tool_args": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The target search query string.",
                }
            },
            "required": ["query"],
        },
        "direct_reply": {
            "type": "string",
            "description": "Your text answer if no web tools are needed.",
        },
    },
    "required": ["action"],
}

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


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
            # FIXED: Passing schema through extra_body["format"] to align with Ollama's API surface
            response = client.chat.completions.create(
                model="gemma4:e2b",
                messages=messages,  # type: ignore
                response_format={"type": "json_object"},
                extra_body={"format": tool_call_schema} if web_search_active else None # type: ignore
            )

            response_json = response.choices[0].message.content
            
            # Double-check against empty returns before decoding
            if not response_json or not response_json.strip():
                raise ValueError("Ollama engine returned an empty response token string.")
                
            decision = json.loads(response_json.strip())

            if decision.get("action") == "execute_tool":
                function_name = decision.get("tool_name")
                function_args = decision.get("tool_args", {})

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

                final_stream_response = client.chat.completions.create(
                    model="gemma4:e2b",
                    messages=messages,  # type: ignore
                    stream=True,
                )

                def generate_stream():
                    for chunk in final_stream_response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content

                return StreamingResponse(
                    generate_stream(), media_type="text/plain"
                )

            else:
                def generate_static_stream():
                    yield decision.get("direct_reply", "No text output returned by the engine.")

                return StreamingResponse(
                    generate_static_stream(), media_type="text/plain"
                )

        else:
            direct_stream = client.chat.completions.create(
                model="gemma4:e2b",
                messages=messages,  # type: ignore
                stream=True,
            )

            def generate_direct_stream():
                for chunk in direct_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            return StreamingResponse(
                generate_direct_stream(), media_type="text/plain"
            )

    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)