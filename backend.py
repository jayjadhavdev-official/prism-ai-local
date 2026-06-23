import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import ollama

from tools.web_search import execute_tool_sync

app = FastAPI(title="Prism AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_SYSTEM = (
    "You are Prism AI, a cutting‑edge assistant with live web access.\n"
    "Today's date is {date}.\n"
    "When the user asks a question that requires real‑time information, the system will inject live web search results. "
    "You MUST base your answer on that data. Never say you don't have access to real‑time data – just use the data you are given. "
    "If the data appears incomplete, answer as helpfully as you can using it."
)


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        body = await request.body()
        data = json.loads(body.decode("utf-8"))
        user_message = data.get("message", "").strip()
        web_search_active = data.get("webSearchActive", False)

        current_date = datetime.now().strftime("%A, %B %d, %Y")
        system_prompt = BASE_SYSTEM.replace("{date}", current_date)

        if web_search_active:
            router_messages = [
                {
                    "role": "system",
                    "content": (
                        "Analyze if the user query requires current real‑time data, dates, weather, news, or a web search. "
                        "If it does, output exactly: <search>refined query</search>. If it does NOT, output: <normal>."
                    ),
                },
                {"role": "user", "content": user_message},
            ]

            router_response = ollama.chat(
                model="gemma4:e2b",
                messages=router_messages,
                options={"temperature": 0.0},
            )
            router_text = router_response.get("message", {}).get("content", "").strip()

            search_query = user_message
            needs_search = False
            if "<search>" in router_text:
                needs_search = True
                try:
                    start = router_text.find("<search>") + len("<search>")
                    end = router_text.find("</search>")
                    if end > start:
                        search_query = router_text[start:end].strip()
                except Exception:
                    pass

            context_data = None
            if needs_search:
                print(f"[ENGINE] Searching for: '{search_query}'")
                context_data = execute_tool_sync(search_query)
                if context_data:
                    print("[ENGINE] Search returned data.")
                else:
                    print("[ENGINE] Search returned no usable data.")

            if needs_search and context_data:
                final_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                    {
                        "role": "user",
                        "content": (
                            "IMPORTANT: The following is LIVE web search data that directly answers the question above. "
                            "You MUST read it and use it to compose your answer. Do NOT ignore it, do NOT say you lack information. "
                            "If the data seems incomplete, answer with what you have.\n\n"
                            f"LIVE SEARCH RESULTS:\n{context_data}"
                        ),
                    },
                ]

                final_stream = ollama.chat(
                    model="gemma4:e2b", messages=final_messages, stream=True
                )

                def generate_search_stream():
                    for chunk in final_stream:
                        yield chunk.get("message", {}).get("content", "")

                return StreamingResponse(generate_search_stream(), media_type="text/plain")

            print("[ENGINE] Falling back to standard chat (no search context).")

        standard_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        direct_stream = ollama.chat(
            model="gemma4:e2b", messages=standard_messages, stream=True
        )

        def generate_direct_stream():
            for chunk in direct_stream:
                yield chunk.get("message", {}).get("content", "")

        return StreamingResponse(generate_direct_stream(), media_type="text/plain")

    except Exception as e:
        print(f"[CRITICAL FAILURE]: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)