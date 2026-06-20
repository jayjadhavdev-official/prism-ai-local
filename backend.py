from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
import json

from tools import get_all_tools, call_tool_by_name

app = FastAPI(title="Showcase Local Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

        messages = [{"role": "user", "content": user_message}]
                
        
        response = client.chat.completions.create(
            model="gemma4:e2b",
            messages=messages,
            tools=get_all_tools(),
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                tool_output = call_tool_by_name(function_name, function_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_output
                })

            final_stream_response = client.chat.completions.create(
                model="gemma4:e2b",
                messages=messages,
                stream=True,
            )

            
            def generate_stream():
                for chunk in final_stream_response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                        
            return StreamingResponse(generate_stream(), media_type="text/plain")
            
        else:
            direct_stream = client.chat.completions.create(
                model = "gemma4:e2b",
                messages=messages,
                stream=True,
            )

            def generate_direct_stream():
                for chunk in direct_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            return StreamingResponse(generate_direct_stream(), media_type="text/plain")

    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
