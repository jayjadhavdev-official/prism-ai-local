import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import ollama

# Pulling our modularized search tool execution loop cleanly
from tools.web_search import execute_tool

app = FastAPI(title="Prism AI Local Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))
        user_message = data.get("message", "hello")
        web_search_active = data.get("webSearchActive", False)

        current_date_str = datetime.now().strftime("%A, %B %d, %Y")
        base_system_prompt = f"You are Prism AI. Current Date: {current_date_str}. Web search tool access: {web_search_active}."

        if web_search_active:
            # Turn 1: High deterministic tag choice for tool requirements
            routing_messages = [
                {
                    "role": "system", 
                    "content": f"{base_system_prompt}\nRespond with exactly '<search>query</search>' if answering requires live web search context. Otherwise answer normally."
                },
                {"role": "user", "content": user_message}
            ]
            
            router_response = ollama.chat(
                model="gemma4:e2b",
                messages=routing_messages,
                options={"temperature": 0.0}
            )

            router_text = router_response.get("message", {}).get("content", "")

            if "<search>" in router_text:
                try:
                    start_idx = router_text.find("<search>") + len("<search>")
                    end_idx = router_text.find("</search>")
                    search_query = router_text[start_idx:end_idx].strip()
                except Exception:
                    search_query = user_message

                print(f"[ENGINE] Intercepted stream. Routing search parameters via MCP module: '{search_query}'")
                
                # Concise execution calling our isolated tool file synchronously
                tool_output = execute_tool(search_query)

                final_messages = [
                    {"role": "system", "content": base_system_prompt},
                    {"role": "user", "content": user_message},
                    {"role": "system", "content": f"Grounded Context verified from local browser lookup:\n{tool_output}"}
                ]
                
                final_stream = ollama.chat(model="gemma4:e2b", messages=final_messages, stream=True)
                
                def generate_stream():
                    for chunk in final_stream:
                        yield chunk.get("message", {}).get("content", "")
                return StreamingResponse(generate_stream(), media_type="text/plain")

        # Fallback normal chat trajectory
        standard_messages = [
            {"role": "system", "content": base_system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        direct_stream = ollama.chat(model="gemma4:e2b", messages=standard_messages, stream=True)

        def generate_direct_stream():
            for chunk in direct_stream:
                yield chunk.get("message", {}).get("content", "")
        return StreamingResponse(generate_direct_stream(), media_type="text/plain")

    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)