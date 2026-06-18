import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

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

        response = client.chat.completions.create(
            model="gemma4:e2b",
            messages=[{"role": "user", "content": user_message}],
            stream=True,
        )

        def generate_stream():
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return StreamingResponse(generate_stream(), media_type="text/plain")

    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
