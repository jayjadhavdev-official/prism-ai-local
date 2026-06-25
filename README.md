# Prism AI Engine

A fully local, privacy‑first conversational AI agent with live web search, short‑term conversation memory, and persistent long‑term user memory. Built with FastAPI, Ollama, and ChromaDB, served as a clean single‑page web interface.


## ✨ Features

- **Agentic Chat** – Streams responses from locally hosted LLMs (Ollama) with full Markdown rendering.
- **Live Web Search** – Toggle real‑time DuckDuckGo search to ground answers in current data.
- **Short‑Term Memory** – Remembers conversation context within the same session (session ID in browser).
- **Long‑Term Memory** – Persistently stores user facts (explicit “remember” triggers) using ChromaDB with semantic retrieval.
- **Self‑Contained Frontend** – Served directly by the backend; no separate web server needed.
- **Built-In HTML and CSS Viewers** - Showcases directly your code (similar to Claude Artifacts).

## 🧱 Project Structure

```
prism_ai_two/
├── backend.py                # FastAPI server, chat endpoint, memory logic
├── frontend/
│   ├── index.html            # Self‑contained chat UI (Tailwind + Marked.js)
│   └── assets/
│       ├── logo.png
│       └── agent-avatar.png
├── tools/
│   ├── web_search.py         # DuckDuckGo search (ddgs library)
│   └── memory_manager.py     # ChromaDB wrapper + explicit memory detection
├── memory_db/                # Persistent ChromaDB storage (auto‑created)
├── requirements.txt          # Python dependencies
└── README.md
```

## 🔧 Prerequisites

- **Python 3.10+** with `pip`
- **Ollama** installed and running with a model (e.g., `gemma4:e2b`)

## 📦 Installation

1. **Clone the repository** or copy the project folder.
2. **Install Python dependencies**:
   ```bash
   pip install fastapi uvicorn ollama chromadb sentence-transformers ddgs
   ```
3. **Pull the Ollama model** (example):
   ```bash
   ollama pull gemma4:e2b
   ```
4. **Ensure assets exist** in `frontend/assets/` (logo and avatar images).

## ⚙️ Configuration

All settings are inside `backend.py`:
- `MAX_HISTORY`: number of conversation turns kept in short‑term memory (default 20).
- `BASE_SYSTEM`: system prompt – you can customise the assistant’s personality.
- The ChromaDB path defaults to `./memory_db`. No external setup required.

## 🚀 Running Locally

1. **Start the backend**:
   ```bash
   python backend.py
   ```
   The server will listen on `http://127.0.0.1:5000`.

2. **Open the UI**:  
   Navigate to `http://127.0.0.1:5000` in your browser.  
   *(Do **not** open `index.html` directly – the backend serves it to make API calls work.)*


## 💬 Usage

### Basic Chat
Type your message and press **Enter** or click **Send**. The response will stream in real time.

### Web Search Toggle
Click the **Web Search: OFF** button to activate live search.  
When enabled, the assistant will:
- Determine if the query needs real‑time data.
- Perform a DuckDuckGo search via the `ddgs` library.
- Inject the top 3 snippets into the prompt (softly, without overriding its own knowledge).

### Memory
- **Short‑term**: The assistant remembers the current conversation as long as the same `sessionId` is used (persists across reloads in the same browser).
- **Long‑term**: Say *“Remember that my name is Alex”*. The system extracts this fact, stores it in ChromaDB, and retrieves it later when relevant – even from a different device or session.

To wipe all stored memories, delete the `memory_db/` folder while the server is stopped.

## 📡 API Reference

### `POST /api/chat`
**Request Body (JSON)**
```json
{
  "message": "What's the weather in London?",
  "webSearchActive": true,
  "sessionId": "optional‑unique‑id"
}
```

- `message` – user input (required)
- `webSearchActive` – boolean to enable web search routing
- `sessionId` – string to identify the conversation session; stored in `localStorage` by the frontend

**Response**: `text/plain` streaming response (chunked tokens).

## 🧠 How the Memory System Works

1. **Explicit Detection**  
   A simple regex (`remember that …`) catches user statements and stores them as long‑term memories.
2. **Semantic Retrieval**  
   Every incoming message is embedded using `all-MiniLM-L6-v2` and the top‑3 most similar memories are fetched from ChromaDB.
3. **Injection**  
   Retrieved memories are added as a system message: *“Relevant user memories (use if helpful): …”*. The assistant can freely use or ignore them.
4. **Conversation History**  
   Last 20 user‑assistant turns are kept in an in‑memory dictionary keyed by `sessionId` and prepended to every call.

## 🔍 Web Search Implementation

The search module (`tools/web_search.py`) tries three strategies in order:
- Instant answer from DuckDuckGo (`answers()`)
- Regular text search snippets (`text()`)
- Fallback simplified query (removing temporal words)

If all fail, the assistant gracefully falls back to standard chat without search data.

## 🎓 Acknowledgements

- [Ollama](https://ollama.com) for local LLM serving
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [ChromaDB](https://www.trychroma.com) for vector memory storage
- [Tailwind CSS](https://tailwindcss.com) and [Marked.js](https://marked.js.org) for the frontend
- [ddgs](https://pypi.org/project/ddgs/) for DuckDuckGo search

---

**Built for design showcases, education, and anyone who wants a private, extendable AI agent.**
## ✨Special Thanks
- Ridhima: Avid and critical benchmarker, helped with countless edits made to this repo