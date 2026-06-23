import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import ollama

from tools import call_tool_by_name

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

        system_prompt = (
            f"You are Prism AI. Current Date: {current_date_str}.\n"
            "You operate under strict structural rules:\n"
            f"Web search tool status: {web_search_active}.\n"
            "If the user asks for real-time information, weather, or events that you do not know, "
            "you MUST use the search tool by writing exactly: <search>your search keywords here</search>.\n"
            "Do not apologize, do not write intro text, just output the tag. If you do not need to search, "
            "respond normally to the user."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        first_stream = ollama.chat(
            model="gemma4:e2b",
            messages=messages,
            stream=True,
            options={"temperature": 0.1} 
        )

        def generate_intercept_stream():
            accumulated_text = ""
            search_triggered = False
            search_query = ""

            for chunk in first_stream:
                content = chunk.get("message", {}).get("content", "")
                accumulated_text += content

                if "<search>" in accumulated_text and not search_triggered:
                    if "</search>" in accumulated_text:
                        search_triggered = True
                        start_idx = accumulated_text.find("<search>") + len("<search>")
                        end_idx = accumulated_text.find("</search>")
                        search_query = accumulated_text[start_idx:end_idx].strip()
                        break
                    else:
                        continue
                
                if "<" not in accumulated_text and not search_triggered:
                    yield content

            if search_triggered and web_search_active:
                print(f"[ENGINE] Intercepted stream. Executing search for: '{search_query}'")
                
                tool_output = call_tool_by_name("web_search", {"query": search_query})

                messages.append({"role": "assistant", "content": f"<search>{search_query}</search>"})
                messages.append({"role": "user", "content": f"Search Results Context:\n{tool_output}"})

                final_stream = ollama.chat(
                    model="gemma4:e2b",
                    messages=messages,
                    stream=True
                )

                for chunk in final_stream:
                    yield chunk.get("message", {}).get("content", "")
            
            elif search_triggered and not web_search_active:
                yield "Web search is currently disabled in your interface panel settings."

        return StreamingResponse(generate_intercept_stream(), media_type="text/plain")

    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)