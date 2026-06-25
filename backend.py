import json
from datetime import datetime

import ollama
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from tools.web_search import execute_tool_sync
from tools.memory_manager import (
    search_memories,
    add_memory,
    extract_explicit_memory_command
)
from tools.weather import get_weather

app = FastAPI(title="Prism AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chosen_model = "llama3.1:8b"

BASE_SYSTEM = (
    "You are Prism AI, a cutting‑edge assistant with live web access.\n"
    "Today's date is {date} and the current time is {time} .\n"
    "You have access to the user's long‑term memories (injected below when relevant). "
    "Use them to personalise your answers.\n"
    "If the user asks you to remember something, confirm and store it.\n"
    "When the user asks a question that requires real‑time information, the system will inject live web search results. "
    "You MUST base your answer on that data. Never say you don't have access to real‑time data – just use the data you are given. "
    "If the data appears incomplete, answer as helpfully as you can using it."
    "If the user asks you to create a web component, landing page, or any visual HTML/CSS example, "
    "output the complete HTML code inside a triple‑backtick block with language 'html'. "
    "The system will automatically render a live preview of that code."
    "Never add a note telling the user to open a browser or view the code externally – the live preview is already shown automatically."
)

MAX_CONTEXT_MESSAGES = 20


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        body = await request.body()
        data = json.loads(body.decode("utf-8"))
        user_message = data.get("message", "").strip()
        web_search_active = data.get("webSearchActive", False)
        history = data.get("history", [])

        now = datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        current_time = now.strftime("%H:%M:%S")
        system_prompt = BASE_SYSTEM.replace("{date}", current_date).replace("{time}", current_time)

        # ---------- Long‑term memory ----------
        mem_text = extract_explicit_memory_command(user_message)
        if mem_text:
            add_memory(mem_text)

        relevant_memories = search_memories(user_message, n_results=3)
        memory_context = ""
        if relevant_memories:
            memory_context = (
                "Relevant user memories (use if helpful):\n" +
                "\n".join(f"- {m}" for m in relevant_memories)
            )

        # ---------- Build base messages ----------
        messages = [{"role": "system", "content": system_prompt}]
        if memory_context:
            messages.append({"role": "system", "content": memory_context})

        recent_history = history[-MAX_CONTEXT_MESSAGES:] if history else []
        messages.extend(recent_history)
        messages.append({"role": "user", "content": user_message})

        if web_search_active:
            router_messages = [
                {
                    "role": "system",
                    "content": (
                        "Analyze if the user query requires current real‑time data, dates, weather, news, or a web search. "
                        "If the user is asking about the weather for a specific location (e.g., 'weather in London'), output exactly: <weather>location name</weather>. "
                        "If the query requires other real‑time data or news, output: <search>refined query</search>. "
                        "If the query does NOT need any real‑time information, output: <normal>."
                    ),
                },
                {"role": "user", "content": user_message},
            ]

            router_response = ollama.chat(
                model=chosen_model,
                messages=router_messages,
                options={"temperature": 0.0},
            )
            router_text = router_response.get("message", {}).get("content", "").strip()

            search_query = user_message
            needs_search = False
            needs_weather = False
            weather_location = ""

            if "<search>" in router_text:
                needs_search = True
                try:
                    start = router_text.find("<search>") + len("<search>")
                    end = router_text.find("</search>")
                    if end > start:
                        search_query = router_text[start:end].strip()
                except Exception:
                    pass

            if "<weather>" in router_text:
                needs_weather = True
                try:
                    start = router_text.find("<weather>") + len("<weather>")
                    end = router_text.find("</weather>")
                    if end > start:
                        weather_location = router_text[start:end].strip()
                except Exception:
                    pass

            # ---------- Weather handling (higher priority) ----------
            if needs_weather and weather_location:
                print(f"[ENGINE] Fetching weather for: '{weather_location}'")
                weather_data = get_weather(weather_location)
                if weather_data:
                    weather_message = {
                        "role": "user",
                        "content": (
                            "The following is live weather data for the requested location. "
                            "Use it to answer the user's question. Do not mention the tool.\n\n"
                            f"WEATHER DATA:\n{weather_data}"
                        ),
                    }
                    final_messages = messages[:-1] + [weather_message, messages[-1]]

                    final_stream = ollama.chat(
                        model=chosen_model, messages=final_messages, stream=True
                    )

                    def generate_weather_stream():
                        for chunk in final_stream:
                            yield chunk.get("message", {}).get("content", "")

                    return StreamingResponse(generate_weather_stream(), media_type="text/plain")
                else:
                    print("[ENGINE] Weather fetch failed. Falling back to standard chat.")
            # ---------- Web Search handling ----------
            elif needs_search:
                print(f"[ENGINE] Searching for: '{search_query}'")
                raw_data = execute_tool_sync(search_query)
                context_data = None
                if raw_data and isinstance(raw_data, str) and not raw_data.startswith("[SEARCH"):
                    context_data = raw_data
                else:
                    print("[ENGINE] Search returned no usable data. Falling back to standard chat.")

                if context_data:
                    search_message = {
                        "role": "user",
                        "content": (
                            "The following is live web search data that may help answer the question. "
                            "If it contains relevant information, you may use it. If not, you may rely on your own knowledge. "
                            "Do not mention the search tool or any technical errors.\n\n"
                            f"SEARCH DATA:\n{context_data}"
                        ),
                    }
                    final_messages = messages[:-1] + [search_message, messages[-1]]

                    final_stream = ollama.chat(
                        model=chosen_model, messages=final_messages, stream=True
                    )

                    def generate_search_stream():
                        for chunk in final_stream:
                            yield chunk.get("message", {}).get("content", "")

                    return StreamingResponse(generate_search_stream(), media_type="text/plain")

        final_stream = ollama.chat(
            model=chosen_model, messages=messages, stream=True
        )

        def generate_direct_stream():
            for chunk in final_stream:
                yield chunk.get("message", {}).get("content", "")

        return StreamingResponse(generate_direct_stream(), media_type="text/plain")

    except Exception as e:
        print(f"[CRITICAL FAILURE]: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)