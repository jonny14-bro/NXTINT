# backend/ai/semantic_engine.py
import os
from backend.app.faiss_manager import FaissManager

SEMANTIC_DIR = "data/semantic"
INDEX = f"{SEMANTIC_DIR}/semantic.faiss"
META  = f"{SEMANTIC_DIR}/semantic_meta.json"

semantic_faiss = FaissManager(dim=384)

def load_semantic():
    if os.path.exists(INDEX):
        semantic_faiss.load(INDEX, META)

def save_semantic():
    semantic_faiss.save(INDEX, META)
    
    
# backend/ai/semantic_engine.py

def detect_timeline_intent(query: str) -> bool:
    """
    Detect whether user is asking for temporal / event-based analysis
    """
    if not query:
        return False

    q = query.lower()

    timeline_keywords = [
        "when",
        "timeline",
        "history",
        "events",
        "sequence",
        "chronology",
        "before",
        "after",
        "first",
        "last",
        "during"
    ]

    return any(k in q for k in timeline_keywords)

