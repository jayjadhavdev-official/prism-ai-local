import chromadb
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime

client = chromadb.PersistentClient(path="./memory_db")

collection = client.get_or_create_collection("prism_memories")

model = SentenceTransformer('all-MiniLM-L6-v2')


def add_memory(text: str, metadata: dict = None) -> str:
    """Store a memory and return its ID."""
    if metadata is None:
        metadata = {}
    metadata["timestamp"] = datetime.now().isoformat()
    mem_id = str(uuid.uuid4())
    embedding = model.encode(text).tolist()
    collection.add(
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata],
        ids=[mem_id]
    )
    return mem_id


def search_memories(query: str, n_results: int = 3) -> list:
    """Return the most relevant memory texts for the given query."""
    if collection.count() == 0:
        return []
    embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    return results.get("documents", [[]])[0]


def extract_explicit_memory_command(user_message: str) -> str | None:
    """Very simple detection: if the message contains 'remember', return the part after it."""
    import re
    lower = user_message.lower()
    if "remember that" in lower or "remember" in lower:
        match = re.search(r'remember\s+(that\s+)?(.+)', user_message, re.IGNORECASE)
        if match:
            return match.group(2).strip()
    return None