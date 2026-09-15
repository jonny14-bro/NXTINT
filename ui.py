# ui.py (only this function changes)
import os
import sys
import json
import time
import shared
import random

# ui.py (BOOTSTRAP LAYER)

from backend.app.faiss_manager import FaissManager
from backend.app.faiss_registry import face_faiss

KNOWN_IDENTITIES = {
    "YOU": None  # reserved
}

FRIEND_COUNTER = 0

def bootstrap():
    
    _load_faiss_index()
    _load_text_faiss_index()
    _load_face_faiss()

    shared.configure(
        faiss_mgr=faiss_manager,
        append_record_fn=_append_osint_record,
        save_faiss_fn=_save_faiss_index,
    )

    shared.configure_text(
        text_faiss_mgr=text_faiss,
        save_text_faiss_fn=_save_text_faiss_index,
    )

# -----------------------------------------------------
# FAISS + DATA DIR INITIALIZATION
# -----------------------------------------------------

# 512-dim FAISS for images + video frames
faiss_manager = FaissManager(dim=512)  # :contentReference[oaicite:1]{index=1}
# 384-dim FAISS for text semantic search
text_faiss = FaissManager(dim=384)     # separate index for MiniLM text embeddings

# Data directory and index/metadata paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
META_PATH = os.path.join(DATA_DIR, "faiss_meta.json")

TEXT_INDEX_PATH = os.path.join(DATA_DIR, "text_index.faiss")
TEXT_META_PATH = os.path.join(DATA_DIR, "text_faiss_meta.json")

OSINT_DB_PATH = os.path.join(DATA_DIR, "osint_records.json")
ADMIN_CONFIG_PATH = os.path.join(DATA_DIR, "admin_config.json")

FACE_INDEX_PATH = os.path.join(DATA_DIR, "face_index.faiss")
FACE_META_PATH = os.path.join(DATA_DIR, "face_faiss_meta.json")

FACE_IDENTITY_PATH = os.path.join(DATA_DIR, "face_identities.json")

DATA_META_DIR = os.path.join(DATA_DIR, "media_metadata")
os.makedirs(DATA_META_DIR, exist_ok=True)



RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
CYAN = "\033[96m"
RESET = "\033[0m"

def startup():
    try:
        from backend.tools.clean import auto_clean
        auto_clean()
    except Exception as e:
        print(f"[WARN] Cleanup skipped: {e}")

def load_identities():
    global KNOWN_IDENTITIES, FRIEND_COUNTER

    KNOWN_IDENTITIES = {}
    FRIEND_COUNTER = 0

    if not os.path.exists(FACE_IDENTITY_PATH):
        return

    if os.path.getsize(FACE_IDENTITY_PATH) == 0:
        return

    try:
        with open(FACE_IDENTITY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            KNOWN_IDENTITIES = data.get("identities", {})
            FRIEND_COUNTER = data.get("counter", 0)
    except json.JSONDecodeError:
        # corrupted / partial file → safe reset
        KNOWN_IDENTITIES = {}
        FRIEND_COUNTER = 0


def _load_osint_db():
    if not os.path.exists(OSINT_DB_PATH):
        return []
    try:
        with open(OSINT_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
    
def _load_faiss_index():
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        try:
            faiss_manager.load(INDEX_PATH, META_PATH)
            print(f"[INFO] Loaded image/video FAISS index with {faiss_manager.count()} items.")
        except Exception as e:
            print(f"[WARN] Could not load FAISS index: {e}")
    else:
        print("[INFO] No existing image/video FAISS index found.")

def _load_text_faiss_index():
    if os.path.exists(TEXT_INDEX_PATH) and os.path.exists(TEXT_META_PATH):
        try:
            text_faiss.load(TEXT_INDEX_PATH, TEXT_META_PATH)
            print(f"[INFO] Loaded text FAISS index with {text_faiss.count()} items.")
        except Exception as e:
            print(f"[WARN] Could not load text FAISS index: {e}")
    else:
        print("[INFO] No existing text FAISS index found; starting empty.")

def _load_face_faiss():
    if os.path.exists(FACE_INDEX_PATH) and os.path.exists(FACE_META_PATH):
        try:
            face_faiss.load(FACE_INDEX_PATH, FACE_META_PATH)
            print(f"[INFO] Loaded face FAISS with {face_faiss.count()} faces.")
        except Exception as e:
            print(f"[WARN] Could not load face FAISS: {e}")

def _save_faiss_index():
    try:
        faiss_manager.save(INDEX_PATH, META_PATH)
    except Exception as e:
        print(f"[WARN] Failed to save FAISS index: {e}")

def _save_text_faiss_index():
    try:
        text_faiss.save(TEXT_INDEX_PATH, TEXT_META_PATH)
    except Exception as e:
        print(f"[WARN] Failed to save text FAISS index: {e}")

def _save_osint_db(records):
    try:
        with open(OSINT_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=4)
    except Exception as e:
        print(f"[WARN] Failed to save OSINT DB: {e}")

def save_identities():
    with open(FACE_IDENTITY_PATH, "w") as f:
        json.dump({
            "identities": KNOWN_IDENTITIES,
            "counter": FRIEND_COUNTER
        }, f, indent=4)

def _append_osint_record(record: dict):
    records = _load_osint_db()
    records.append(record)
    _save_osint_db(records)

# -----------------------------------------------------
# BANNER
# -----------------------------------------------------
def banner1():
    print(RED + BOLD +    """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣷⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡔⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠭⣿⣿⣿⣶⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⣾⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡿⣿⡿⣿⣿⣿⣿⣦⣴⣶⣶⣶⣶⣦⣤⣤⣀⣀⠀⠀⠀⠀⠀⢀⣀⣤⣲⣿⣿⣿⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⡝⢿⣌⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣤⣾⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠲⡝⡷⣮⣝⣻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣛⣿⣿⠿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣦⣝⠓⠭⣿⡿⢿⣿⣿⣛⠻⣿⠿⠿⣿⣿⣿⣿⣿⣿⡿⣇⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣤⡀⠈⠉⠚⠺⣿⠯⢽⣿⣷⣄⣶⣷⢾⣿⣯⣾⣿⠿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⡟⠀⠀⣴⣿⣿⣼⠈⠉⠃⠋⢹⠁⢀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢿⣿⡟⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⣀⣀⣀⣀⣴⣿⣿⡿⣿⠀⠀⠀⠀⠇⠀⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⢿⢿⣾⣿⣿⡿⠿⠿⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠿⢿⡄⢦⣤⣤⣶⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠘⠛⠋⠁⠁⣀⢉⡉⢻⡻⣯⣻⣿⢻⣿⣀⠀⠀⠀⢠⣾⣿⣿⣿⣹⠉⣍⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠠⠔⠒⠋⠀⡈⠀⠠⠤⠀⠓⠯⣟⣻⣻⠿⠛⠁⠀⠀⠣⢽⣿⡻⠿⠋⠰⠤⣀⡈⠒⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠔⠊⠁⠀⣀⠔⠈⠁⠀⠀⠀⠀⠀⣶⠂⠀⠀⠀⢰⠆⠀⠀⠀⠈⠒⢦⡀⠉⠢⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠊⠀⠀⠀⠀⠎⠁⠀⠀⠀⠀⠀⠀⠀⠀⠋⠀⠀⠀⠰⠃⠀⠀⠀⠀⠀⠀⠀⠈⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠿⠭⠯⠭⠽⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """ + RESET)
    
    
def banner2():
    print(RED + BOLD +   """
       ⠀⠀⠀⠀        ⠀⠀⠀⢰⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡄⠀⠀⠀
⠀⠀⠀    ⠀⠀⠀         ⠀⠀⣼⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣿⡇⠀⠀⠀
⠀⠀⠀⠀⠀             ⠀⠀⠀⣿⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⡇⠀⠀⠀
⠀⠀⠀⠀⠀             ⠀⠀⠀⣿⣿⣿⣿⣷⡀⢀⣀⣀⣀⣀⠀⠀⣠⣿⣿⣿⣿⡇⠀⠀⠀
⠀⠀⠀              ⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣿⣿⣿⣿⣿⠀⠀⠀⠀
⠀⠀             ⠀   ⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀
⠀⠀             ⠀⠀ ⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢿⣿⣿⣿⣿⣿⣿⣏⠀⠀⠀⠀
⠀⠀               ⠀⠀⠀⢶⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠁⠀⠀⠙⢿⣿⣿⠁⠙⣿⣧⡀⠀⠀
⠀              ⠀⢀⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣧⡀⠐⠻⣷⣦⡀⠈⢻⣿⣀⣴⢼⣿⡷⠀⠀
              ⣴⣾⣿⣿⣿⡿⣿⣿⡟⠟⠁⢻⣿⣿⣷⣦⣄⣀⡀⠈⠀⠀⠙⢿⣦⣼⣿⣷⠀⠀
              ⣿⣿⣿⣿⣿⡇⠈⠋⠀⠀⠀⠈⠛⠛⠛⠛⠉⠁⠀⠀⠀⠀⠀⠀⠙⣿⣿⡏⠀⠀
              ⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠿⢿⣆⡀
              ⢹⣿⣿⣿⣿⡇⣠⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⠟
               ⠘⣿⣿⣿⣿⣿⡏⢀⠀⠀⠀⠀⠀⠘⠿⣿⣿⡿⢿⣷⣦⣄⡀⠀⠀⢀⣼⡟⠁⠀
               ⠀⢹⣿⣿⣿⣿⣧⡏⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣦⣄⠙⠋⠛⡕⠒⠛⠛⠀⠀⠀
               ⠀⠀⢻⣿⣿⣿⣿⡇⢀⠀⠀⠀⠀⣀⣠⣤⣤⣄⡉⠻⣷⣤⣆⣀⡴⠀⠀⠀⠀⠀
⠀⠀               ⠀⠹⣿⣿⣿⣷⣿⠀⠀⠀⠈⠁⠀⠛⠛⠛⣿⣷⣌⠛⠛⠛⠁⠀⠀⠀⠀⠀
⠀⠀⠀               ⠀⠘⢿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀              ⠙⠿⣿⡄⠀⠀⠀⠀⢀⣴⣴⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀              ⠀⠈⠁⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⠛⠇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀              ⠀⠀⠀⠛⠻⠿⠿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

  """ + RESET )
  
  
def banner3():
    print(RED + BOLD +   """
                  ⠀   ⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⣀⣠⣤⣶⣶⣶⣶⣶⣶⣶⣦⣀⠀⠀⠀⠀⢀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀
⠀     ⠀                ⠀⠀ ⠀⠀⢠⢤⣠⣶⣿⣿⡿⠿⠛⠛⠛⠛⠉⠛⠛⠛⠛⠿⣷⡦⠞⣩⣶⣸⡆⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀                  ⠀ ⠀⠀⣠⣾⡤⣌⠙⠻⣅⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠔⠋⢀⣾⣿⣿⠃⣇⠀⠀⠀⠀⠀⠀⠀
      ⠀                 ⠀⣠⣾⣿⡟⢇⢻⣧⠄⠀⠈⢓⡢⠴⠒⠒⠒⠒⡲⠚⠁⠀⠐⣪⣿⣿⡿⡄⣿⣷⡄⠀⠀⠀⠀⠀
⠀                   ⠀ ⣠⣿⣿⠟⠁⠸⡼⣿⡂⠀⠀⠈⠁⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠉⠹⣿⣧⢳⡏⠹⣷⡄⠀⠀⠀⠀
                 ⠀⠀⣰⣿⡿⠃⠀⠀⠀⢧⠑⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⠇⡸⠀⠀⠘⢿⣦⣄⠀⠀
                 ⠀⢰⣿⣿⠃⠀⠀⠀⠀⡼⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡠⠀⠀⠀⠀⠀⠀⠰⡇⠀⠀⠀⠈⣿⣿⣆⠀
                 ⠀⣿⣿⡇⠀⠀⠀⠀⢰⠇⠀⢺⡇⣄⠀⠀⠀⠀⣤⣶⣀⣿⠃⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠸⣿⣿⡀
                 ⢸⣿⣿⠀⠀⠀⠀⠀⢽⠀⢀⡈⠉⢁⣀⣀⠀⠀⠀⠉⣉⠁⠀⠀⠀⣀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⣿⣿⡇
                 ⢸⣿⡟⠀⠀⠀⠠⠀⠈⢧⡀⠀⠀⠀⠹⠁⠀⠀⠀⠀⠀⠀⠠⢀⠀⠀⠀⠀⠀⢼⠁⠀⠀⠀⠀⠀⢹⣿⡇
                 ⢸⣿⣿⠀⠀⠀⠀⠀⠠⠀⠙⢦⣀⠠⠊⠉⠂⠄⠀⠀⠀⠈⠀⠀⠀⣀⣤⣤⡾⠘⡆⠀⠀⠀⠀⠀⣾⣿⡇
                 ⠘⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⢠⠜⠳⣤⡀⠀⠀⣀⣤⡤⣶⣾⣿⣿⣿⠟⠁⠀⠀⡸⢦⣄⠀⠀⢀⣿⣿⠇
                 ⠀⢿⣿⣧⠀⠀⠀⠀⠀⣠⣤⠞⠀⠀⠀⠙⠁⠙⠉⠀⠀⠸⣛⡿⠉⠀⠀⠀⢀⡜⠀⠀⠈⠙⠢⣼⣿⡿⠀
⠀                 ⠈⣿⣿⣆⠀⠀⢰⠋⠡⡇⠀⡀⣀⣤⢢⣤⣤⣀⠀⠀⣾⠟⠀⠀⠀⠀⢀⠎⠀⠀⠀⠀⠀⣰⣿⣿⠁⠀
⠀⠀                 ⠈⢿⣿⣧⣀⡇⠀⡖⠁⢠⣿⣿⢣⠛⣿⣿⣿⣷⠞⠁⠀⠀⠈⠫⡉⠁⠀⠀⠀⠀⢀⣼⣿⠿⠃⠀⠀
⠀⠀⠀                 ⠈⠻⣿⣿⣇⡀⡇⠀⢸⣿⡟⣾⣿⣿⣿⣿⠋⠀⠀⠀⢀⡠⠊⠁⠀⠀⠀⢀⣠⣿⠏⠀⠀⠀⠀⠀
⠀⠀⠀       ⠀⠀           ⠈⠻⣿⣿⣦⣀⢸⣿⢻⠛⣿⣿⡿⠁⠀⠀⣀⠔⠉⠀⠀⠀⠀⣀⣴⡿⠟⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀       ⠀⠀⠀           ⠀⠈⠙⠿⣿⣿⣿⣼⣿⣿⣟⠀⠀⡠⠊⠀⣀⣀⣠⣴⣶⠿⠟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀      ⠀⠀⠀⠀ ⠀           ⠀⠀⠙⠛⠿⣿⣿⣿⣿⣶⣶⣷⣶⣶⡿⠿⠛⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀       ⠀⠀⠀ ⠀⠀⠀         ⠀⠀⠀⠀⠀⠉⠉⠛⠛⠛⠛⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

  """ + RESET )


def banner4():
    print( RED + BOLD +    """
                            -`                     IUseArchbtw@arch
                           .o+`                    ----------------
                          `ooo/                    OS: Arch linux x86_64
                         `+oooo:                   Model: ASUS TUF Gaming F15 FX506HC_FX506HC 1.0
                        `+oooooo:                  Kernel: 6.8.5-zen1-1-zen
                        -+oooooo+:                 Uptime: 7 hours, 49 mins
                      `/:-:++oooo+:                Packages 1244 (pacman), 13 (flatpak)
                     `/++++/+++++++:               Shell: bash 5.2.26
                    `/++++++++++++++:              Resolution: 1920x1080
                   `/+++ooooooooooooo/`            DE: LXQt 1.4.0
                  ./ooosssso++osssssso+`           WM: Openbox
                 .oossssso-````/ossssss+`          Theme: Breeze [GTK2/3]
                -osssssso.      :ssssssso.         Icons: breeze [GTK2/3]
               :osssssss/        osssso+++.        Terminal: qterminal
              /ossssssss/        +ssssooo/-        Terminal Font: Source Code Pro 12
            `/ossssso+/:-        -:/+osssso+-      CPU: 11th Gen Intel 15-11400H (12) @ 4.500GHz
           `+sso+:-`                 `.-/+oso:     GPU: NVIDIA GeForce RTX 3050 Mobile
          `++:.                           `-/+/    Memory: 8546 / 15731MiB
           .`                                 ` 
                                                   ⬛🟥🟩🟫🟦🟪🟦⬛
                                                   🟩🟥🟩🟨🟦🟪🟦⬜
    
    """ + RESET )


def banner5():
    print( RED + BOLD +   """
            ⠀⠀⠀⠀⠀⠀⠀⢀⠆⠀⢀⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡀⠀⠰⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀    ⠀        ⠀⠀⠀⢠⡏⠀⢀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⡀⠀⢹⣄⠀⠀⠀⠀⠀⠀
⠀            ⠀⠀⠀⠀⣰⡟⠀⠀⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣧⠀⠀⢻⣆⠀⠀⠀⠀⠀
    ⠀⠀⠀        ⠀⢠⣿⠁⠀⣸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣇⠀⠈⣿⡆⠀⠀⠀⠀
⠀            ⠀⠀⠀⣾⡇⠀⢀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡀⠀⢸⣿⠀⠀⠀⠀
            ⠀⠀⠀⢸⣿⠀⠀⣸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣇⠀⠀⣿⡇⠀⠀⠀
            ⠀⠀⠀⣿⣿⠀⠀⣿⣿⣧⣤⣤⣤⣤⣤⣤⡀⠀⣀⠀⠀⣀⠀⢀⣤⣤⣤⣤⣤⣤⣼⣿⣿⠀⠀⣿⣿⠀⠀⠀
            ⠀⠀⢸⣿⡏⠀⠀⠀⠙⢉⣉⣩⣴⣶⣤⣙⣿⣶⣯⣦⣴⣼⣷⣿⣋⣤⣶⣦⣍⣉⡉⠋⠀⠀⠀⢸⣿⡇⠀⠀
            ⠀⠀⢿⣿⣷⣤⣶⣶⠿⠿⠛⠋⣉⡉⠙⢛⣿⣿⣿⣿⣿⣿⣿⣿⡛⠛⢉⣉⠙⠛⠿⠿⣶⣶⣤⣾⣿⡿⠀⠀
⠀    ⠀        ⠀⠙⠻⠋⠉⠀⠀⠀⣠⣾⡿⠟⠛⣻⣿⣿⣿⣿⣿⣿⣿⣿⣟⠛⠻⢿⣷⣄⠀⠀⠀⠉⠙⠟⠋⠀⠀⠀
    ⠀⠀⠀⠀⠀        ⠀⠀⢀⣤⣾⠿⠋⢀⣠⣾⠟⢫⣿⣿⣿⣿⣿⣿⡍⠻⣷⣄⡀⠙⠿⣷⣤⡀⠀⠀⠀⠀⠀⠀⠀
⠀    ⠀⠀        ⠀⠀⣠⣴⡿⠛⠁⠀⢸⣿⣿⠋⠀⢸⣿⣿⣿⣿⣿⣿⡗⠀⠙⣿⣿⡇⠀⠈⠛⢿⣦⣄⠀⠀⠀⠀⠀
            ⢀⠀⣀⣴⣾⠟⠋⠀⠀⠀⠀⢸⣿⣿⠀⠀⢸⣿⣿⣿⣿⣿⣿⡇⠀⠀⣿⣿⡇⠀⠀⠀⠀⠙⠻⣷⣦⣀⠀⣀
            ⢸⣿⣿⠋⠁⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠈⣿⣿⣿⣿⣿⣿⠁⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠈⠙⣿⣿⡟
            ⢸⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⢹⣿⣿⣿⣿⡏⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⡇
            ⢸⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⢿⣿⣿⡿⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⡇
            ⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⠀⠈⠿⠿⠁⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀
            ⠀⢻⣿⡄⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⢀⣿⡟⠀
            ⠀⠘⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠃⠀
    ⠀⠀        ⠸⣷⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⣾⠏⠀⠀
⠀            ⠀⠀⢻⡆⠀⠀⠀⠀⠀⠀⠀⠸⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⠇⠀⠀⠀⠀⠀⠀⠀⢰⡟⠀⠀⠀
⠀⠀            ⠀⠀⢷⠀⠀⠀⠀⠀⠀⠀⠀⢿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡿⠀⠀⠀⠀⠀⠀⠀⠀⡾⠀⠀⠀⠀
⠀⠀⠀            ⠀⠈⢧⠀⠀⠀⠀⠀⠀⠀⠸⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⠇⠀⠀⠀⠀⠀⠀⠀⡸⠁⠀⠀⠀⠀
⠀⠀⠀⠀⠀            ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⢰⡟⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀            ⠀⠀⠀⠀⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⡞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀            ⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠜⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """ + RESET )

def banner6():
    print( RED + BOLD + """
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⢠⣤⡲⣤⢂⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣶⡽⣮⣻⣯⣿⢿⣷⣾⣿⣿⣶⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⢿⣻⣿⣿⣿⣿⣿⣿⣿⣻⡷⣟⠾⣹⣗⣇⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣾⣿⣿⣿⣿⣹⣷⣿⣿⣿⣿⣿⡾⣷⢹⡾⢿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⢱⣿⢿⣿⣿⠷⣿⢿⣶⡷⣿⢾⡷⣷⡿⢦⣿⠷⣦⣳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢸⣻⣟⣿⣿⣿⣿⣿⣻⣿⣿⣿⣟⣿⣿⣿⣿⣿⣾⢯⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⡺⣹⣿⣯⣼⣷⣿⢻⠿⣷⣿⢾⣟⡭⠻⣾⣿⣾⡿⠢⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠎⠁⠀⠀⠀⠀⠈⠻⠻⣭⣻⠗⠋⠁⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⣸⡗⠀⠀⠀⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣄⡀⠀⠀⢀⣀⠀⠀⠰⡿⣏⣀⣀⡀⠀⠀⠀⣀⣠⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣯⢿⣾⡿⣟⡆⠀⠘⣷⣻⣟⢯⣙⡾⣭⢻⢿⡽⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣏⡿⣾⣟⣿⠇⠀⠈⠾⣷⣎⡿⣮⡽⣞⣷⣾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣇⣿⣿⢿⡈⠀⠀⠀⢷⣸⡸⡉⢷⡹⡾⣹⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⣿⢿⡯⠁⠀⠀⠀⠀⠉⠁⣳⡾⢽⣃⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠛⠁⠀⠀⠀⠀⢀⣠⡶⣿⠙⢏⢷⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠛⠙⠛⠙⠋⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠠⠄⠀⠀⠈⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """ + RESET )

def banner():
    print(
        BOLD +
        """          
                    ██████╗ """ + RED + """███████╗""" + RESET + BOLD + """██╗███╗   ██╗████████╗
                   ██╔═══██╗""" + RED + """██╔════╝""" + RESET + BOLD + """██║████╗  ██║╚══██╔══╝
                   ██║   ██║""" + RED + """███████╗""" + RESET + BOLD + """██║██╔██╗ ██║   ██║   
                   ██║   ██║""" + RED + """╚════██║""" + RESET + BOLD + """██║██║╚██╗██║   ██║   
                   ╚██████╔╝""" + RED + """███████║""" + RESET + BOLD + """██║██║ ╚████║   ██║   
                    ╚═════╝ """ + RED + """╚══════╝""" + RESET + BOLD + """╚═╝╚═╝  ╚═══╝   ╚═╝   


                      ☠☠☠  D A N G E R   Z O N E  ☠☠☠
                     UNAUTHORIZED ACCESS = TERMINATION

                             PS1 OSINT SCANNER
    """ + RESET
    )
    


def scan_image_ui():
    path = input("Enter image file path: ").strip()

    print("[*] Scanning image...")
    try:
        result = shared.scan_image(path)

        print("[RESULT] Image Analysis:")
        print(json.dumps(
            {
                "filename": result["filename"],
                "exif": result["exif"],
                "embedding_len": result["embedding_len"]
            },
            indent=4
        ))

        if result["matches"]:
            print("[INFO] Similar items found:")
            for rid, dist, meta in result["matches"]:
                mtype = meta.get("type", "unknown")
                fname = meta.get("filename") or meta.get("frame") or "N/A"
                src = meta.get("source")
                print(
                    f"  - [{mtype}] {fname} "
                    f"(source: {src}) (distance: {dist:.6f})"
                )
        else:
            print("[INFO] No similar items found.")

    except FileNotFoundError:
        print("[ERROR] File does not exist.")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")



# ui.py (replace only scan_video_ui)


def scan_video_ui():
    path = input("Enter video file path: ").strip()

    print("[*] Scanning video frames...")
    try:
        result = shared.scan_video(path)

        if not result["frames"]:
            print("[INFO] No frames extracted.")
            return

        print(f"[INFO] Processed {len(result['frames'])} frames.")

        if result["faces"]:
            print(f"[INFO] Detected {len(result['faces'])} faces across frames.")
            for f in result["faces"]:
                print(
                    f"  - Frame: {f['frame']} | "
                    f"BBox: {f['bbox']} | "
                    f"UID: {f['face_uid']}"
                )
        else:
            print("[INFO] No faces detected in video.")

    except FileNotFoundError:
        print("[ERROR] File does not exist.")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")


# ui.py (Git Scan UI)


def scan_git_ui():
    path = input("Enter local Git repository path: ").strip()

    print("[*] Scanning Git repository for secrets...")
    try:
        result = shared.scan_git_repo(path)

        print("\n[RESULT] Git Repository Scan")
        print(f"Repository : {result['path']}")
        print(f"Findings   : {result['total_findings']}")

        if result["total_findings"] == 0:
            print("[✔] No secrets detected.")
            return

        print("\n[DETECTED ISSUES]")
        for idx, item in enumerate(result["findings"], start=1):
            ftype = item.get("type", "unknown")
            file = item.get("file", "unknown")
            line = item.get("line", "N/A")
            severity = item.get("severity", "unknown")

            print(f"\n[{idx}] {ftype.upper()}")
            print(f"  File     : {file}")
            print(f"  Line     : {line}")
            print(f"  Severity : {severity}")

    except FileNotFoundError:
        print("[ERROR] Repository path does not exist.")
    except ValueError as e:
        print(f"[ERROR] {e}")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")


# ui.py (Text Scan UI)


def scan_text_ui():
    path = input("Enter text file path: ").strip()

    print("[*] Scanning text file...")
    try:
        result = shared.scan_text(path)

        print("\n[RESULT] Text Analysis")
        print(f"File      : {result['path']}")
        print(f"Length    : {result['length']} characters")
        print(f"FAISS UID : {result['faiss_uid']}")

        print("[✔] Text indexed for semantic intelligence.")

    except FileNotFoundError:
        print("[ERROR] File does not exist.")
    except ValueError as e:
        print(f"[ERROR] {e}")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")




# ui.py (Audio Scan UI)


def scan_audio_ui():
    path = input("Enter audio file path: ").strip()

    print("[*] Scanning audio file...")
    try:
        result = shared.scan_audio(path)
        analysis = result["analysis"]

        print("\n[RESULT] Audio Analysis")
        print(f"File        : {result['path']}")
        print(f"Duration    : {analysis.get('duration')} sec")
        print(f"Codec       : {analysis.get('codec')}")
        print(f"Sample Rate : {analysis.get('sample_rate')}")
        print(f"Channels    : {analysis.get('channels')}")

        if analysis.get("transcript"):
            print("\n[TRANSCRIPT]")
            print(analysis["transcript"])

        if analysis.get("keywords"):
            print("\n[KEYWORDS]")
            for k in analysis["keywords"]:
                print(f"  - {k}")

    except FileNotFoundError:
        print("[ERROR] File does not exist.")
    except ValueError as e:
        print(f"[ERROR] {e}")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")





def scan_image_advanced_ui():
    path = input("Enter image file path (ADVANCED): ").strip()

    print("[*] Running advanced image intelligence scan...")
    try:
        result = shared.scan_image_advanced(path)

        print("\n[INTELLIGENCE SUMMARY]")
        for note in result["intelligence_notes"]:
            print(f" - {note}")

        if result["faces"]:
            print("\n[FACE ANALYSIS]")
            for idx, f in enumerate(result["faces"], start=1):
                print(f"\n[FACE {idx}]")
                print(f"  BBox      : {f['bbox']}")
                print(f"  Identity  : {f['identity']}")
                print(f"  Confidence: {f['confidence']}%")

        else:
            print("\n[INFO] No faces to analyze.")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")



def scan_video_advanced_ui():
    path = input("Enter video file path (ADVANCED): ").strip()

    print("[*] Running advanced video intelligence scan...")
    try:
        result = shared.scan_video_advanced(path)

        print("\n[VIDEO INTELLIGENCE SUMMARY]")
        print(f"Frames processed : {result['frames_processed']}")
        print(f"Faces detected   : {result['faces_detected']}")

        for note in result["intelligence_notes"]:
            print(f" - {note}")

        if result["identities"]:
            print("\n[IDENTITIES FOUND]")
            for i in result["identities"]:
                print(
                    f"• {i['identity']} | "
                    f"Avg confidence: {i['avg_confidence']}% | "
                    f"Frames: {i['frames_seen']} | "
                    f"Best frame: {i['best_frame']}"
                )
        else:
            print("\n[INFO] No confirmed identities.")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")




def enroll_face_ui():
    print("\n[FACE ENROLLMENT]")
    print("⚠️ Enrollment is permanent and should be used carefully.\n")

    path = input("Enter image path for enrollment: ").strip()
    identity = input("Enter identity name (e.g. JOHN_DOE): ").strip()

    if not identity:
        print("[ERROR] Identity name cannot be empty.")
        return

    confirm = input(
        f"Confirm enrollment of '{identity}' from this image? (YES to confirm): "
    ).strip()

    if confirm != "YES":
        print("[INFO] Enrollment cancelled.")
        return

    try:
        result = shared.enroll_face(path, identity)

        print("\n[ENROLLMENT SUCCESS]")
        print(f"Identity : {result['identity']}")
        print(f"Face UID : {result['uid']}")
        print(f"BBox     : {result['bbox']}")

    except Exception as e:
        print(f"[ENROLLMENT FAILED] {e}")

def identity_correlation_ui():
    print("\n[IDENTITY CORRELATION]")
    identity = input("Enter identity name: ").strip()

    if not identity:
        print("[ERROR] Identity cannot be empty.")
        return

    print("[*] Correlating identity across intelligence layers...")

    try:
        records = _load_osint_db()

        evidence = []
        sources = set()
        confidences = []
        timestamps = []

        for r in records:
            # ✅ FIX 1: read identity_evidence records
            if r.get("type") == "identity_evidence" and r.get("identity") == identity:
                evidence.append(r)
                sources.add(r.get("source"))
                confidences.append(r.get("avg_confidence", 0))
                timestamps.append(r.get("timestamp"))

            # ✅ also allow legacy embedded identity
            elif r.get("identity") == identity:
                evidence.append(r)
                sources.add(r.get("source"))
                if "confidence" in r:
                    confidences.append(r["confidence"])
                if "timestamp" in r:
                    timestamps.append(r["timestamp"])

        if not evidence:
            print("[INFO] No evidence found.")
            return

        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

        print("\n[IDENTITY PROFILE]")
        print(f"Identity        : {identity}")
        print(f"Confidence      : {avg_conf}%")
        print(f"Evidence count  : {len(evidence)}")
        print(f"Unique sources  : {len(sources)}")
        print(f"Enrolled        : YES")  # inferred from evidence

        if timestamps:
            print(f"First seen      : {min(timestamps)}")
            print(f"Last seen       : {max(timestamps)}")

        print("\n[SOURCES]")
        for s in sources:
            print(f" - {s}")

        print("\n[EVIDENCE]")
        for e in evidence:
            print(
                f" • Source: {e.get('source')} | "
                f"Frames: {e.get('frames_seen', 'N/A')} | "
                f"Confidence: {e.get('avg_confidence', 'N/A')}%"
            )

    except Exception as e:
        print(f"[FATAL ERROR] {e}")



'''

def identity_correlation_ui():
    print("\n[IDENTITY CORRELATION]")
    identity = input("Enter identity name: ").strip()

    if not identity:
        print("[ERROR] Identity cannot be empty.")
        return

    print("[*] Correlating identity across intelligence layers...")
    try:
        result = shared.correlate_identity(identity)

        if result.get("status") == "NO_EVIDENCE":
            print("[INFO] No evidence found.")
            return

        print("\n[IDENTITY PROFILE]")
        print(f"Identity        : {result['identity']}")
        print(f"Confidence      : {result['confidence']}%")
        print(f"Faces detected  : {result['faces_detected']}")
        print(f"Unique sources  : {result['unique_sources']}")
        print(f"Enrolled        : {'YES' if result['enrolled'] else 'NO'}")

        if result["first_seen"]:
            print(f"First seen      : {result['first_seen']}")
        if result["last_seen"]:
            print(f"Last seen       : {result['last_seen']}")

        print("\n[SOURCES]")
        for s in result["sources"]:
            print(f" - {s}")

        print("\n[EVIDENCE]")
        for e in result["evidence"]:
            print(f" • Source: {e['source']} | bbox: {e['bbox']}")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
'''

def person_timeline_ui():
    print("\n[PERSON TIMELINE]")
    identity = input("Enter identity name: ").strip()

    if not identity:
        print("[ERROR] Identity cannot be empty.")
        return

    print("[*] Building person-centric timeline...")
    try:
        timeline = shared.build_person_timeline(identity)

        if not timeline:
            print("[INFO] No timeline events found for this identity.")
            return

        print(f"\n[Timeline for {identity}]\n")

        for evt in timeline:
            ts = evt.get("timestamp") or "UNKNOWN TIME"
            print(f"🕒 {ts}")
            print(f"   📌 {evt['event_type']}")
            if evt.get("source"):
                print(f"   📂 Source: {evt['source']}")
            if evt.get("description"):
                print(f"   📝 {evt['description']}")
            print("-" * 50)

    except Exception as e:
        print(f"[FATAL ERROR] {e}")




def exposure_graph_ui():
    print("\n[EXPOSURE GRAPH]")
    print("Tip:")
    print(" - Press Enter → full graph")
    print(" - Enter identity name → focused exposure\n")

    identity = input("Filter by identity (optional): ").strip()
    identity = identity if identity else None

    print("[*] Building exposure graph...")
    try:
        graph = shared.build_exposure_graph(identity)

        if not graph["edges"]:
            print("[INFO] No exposure relationships found.")
            return

        print("\n[IDENTITY → SOURCE LINKS]\n")

        for node, links in graph["edges"].items():
            if not node.startswith("IDENTITY:"):
                continue

            print(f"🧩 {node.replace('IDENTITY:', '')}")
            for l in links:
                if l.startswith("SOURCE:"):
                    print(f"   ├── {l.replace('SOURCE:', '')}")
            print()

        # Identity-to-identity inference
        print("\n[IDENTITY CO-EXPOSURE]\n")
        co = {}

        for id_node in graph["identities"]:
            linked_sources = set(graph["edges"].get(id_node, []))
            for other in graph["identities"]:
                if other == id_node:
                    continue
                common_sources = linked_sources & set(graph["edges"].get(other, []))
                if common_sources:
                    co.setdefault(id_node, set()).add(other)

        if not co:
            print("[INFO] No co-exposure between identities.")
        else:
            for k, v in co.items():
                print(f"{k.replace('IDENTITY:', '')}")
                for o in v:
                    print(f"   ↔ {o.replace('IDENTITY:', '')}")
                print()

    except Exception as e:
        print(f"[FATAL ERROR] {e}")




def generate_report_ui():
    print("\n[INTELLIGENCE REPORT GENERATION]")
    identity = input("Enter identity name for report: ").strip()

    if not identity:
        print("[ERROR] Identity cannot be empty.")
        return

    print("[*] Generating intelligence report...")
    try:
        report = shared.generate_identity_report(identity)

        print("\n[REPORT GENERATED]")
        print(f"Report ID   : {report['report_id']}")
        print(f"Identity    : {report['scope']['identity']}")
        print(f"Confidence  : {report['summary']['confidence']}%")
        print(f"Generated at: {report['generated_at']}")

        save = input("\nSave report to file? (y/n): ").strip().lower()
        if save == "y":
            filename = f"{report['report_id']}.json"
            with open(filename, "w") as f:
                json.dump(report, f, indent=4)
            print(f"[✔] Report saved as {filename}")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")



def semantic_search_ui():
    print("\n[SEMANTIC SEARCH]")
    query = input("Enter search query: ").strip()

    if not query:
        print("[ERROR] Query cannot be empty.")
        return

    try:
        top_k = input("Number of results (default 5): ").strip()
        top_k = int(top_k) if top_k else 5

        print("[*] Performing semantic search...")

        # 🔑 HYBRID QUERY (detection + semantic)
        result = shared.hybrid_text_query(query, top_k)

        # -------------------------------------------------
        # DETECTION MODE (secrets / emails / passwords)
        # -------------------------------------------------
        if result.get("mode") == "DETECTION":
            print("\n[DETECTION RESULTS]")

            detections = result.get("detections", [])

            if not detections:
                print("No sensitive entities detected.")
                return

            for item in detections:
                print(f"\nSource: {item['source']}")
                print(f"Length: {item['length']}")

                for k, v in item["findings"].items():
                    print(f"  {k.upper():<12}: {len(v)} detected")

                print("-" * 40)

            return

        # -------------------------------------------------
        # SEMANTIC MODE (contextual search only)
        # -------------------------------------------------
        semantic_results = result.get("results", [])

        if not semantic_results:
            print("[INFO] No matching results found.")
            return

        print(f"\n[RESULTS for '{query}']\n")

        MIN_SCORE = 0.25  # 🚫 ignore weak noise

        shown = 0
        for idx, (uid, score, meta) in enumerate(semantic_results, start=1):
            if score < MIN_SCORE:
                continue

            print(f"[{idx}] Score : {round(score, 6)}")
            print(f"     Source: {meta.get('source')}")
            print(f"     Length: {meta.get('length')}")
            print("-" * 40)

            shown += 1

        if shown == 0:
            print("[INFO] No results above confidence threshold.")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")





def global_search_ui():
    print("\n[GLOBAL SEARCH]")
    query = input("Enter search term (identity, keyword, filename, etc.): ").strip()

    if not query:
        print("[ERROR] Query cannot be empty.")
        return

    print("[*] Searching across all intelligence layers...")
    try:
        result = shared.global_search(query)
        matches = result["matches"]

        found_any = False

        if matches["identities"]:
            found_any = True
            print("\n[IDENTITIES]")
            for i in matches["identities"]:
                print(f" - {i}")

        if matches["sources"]:
            found_any = True
            print("\n[SOURCES]")
            for s in matches["sources"]:
                print(f" - {s}")

        for section, title in [
            ("images", "IMAGES"),
            ("videos", "VIDEOS"),
            ("text", "TEXT FILES"),
            ("git", "GIT REPOS"),
            ("audio", "AUDIO FILES"),
            ("reports", "REPORTS"),
            ("other", "OTHER RECORDS"),
        ]:
            items = matches[section]
            if items:
                found_any = True
                print(f"\n[{title}]")
                for idx, item in enumerate(items, start=1):
                    src = item.get("source")
                    rtype = item.get("type")
                    print(f"[{idx}] Type: {rtype} | Source: {src}")

        if not found_any:
            print("[INFO] No matches found across intelligence layers.")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")

def admin_panel_ui():
    # -------------------------------------------------
    # 🔐 ADMIN AUTHENTICATION (session-based, 3 attempts)
    # -------------------------------------------------
    print("\n🔐 ADMIN AUTHENTICATION REQUIRED")

    MAX_ATTEMPTS = 3
    for attempt in range(MAX_ATTEMPTS):
        pwd = input("Enter admin password: ").strip()
        try:
            if shared.verify_admin_password(pwd):
                print("[ACCESS GRANTED]\n")
                break
            else:
                print("[DENIED] Incorrect password.")
        except Exception as e:
            print(f"[ERROR] {e}")
            return
    else:
        print("[LOCKED] Too many failed attempts. Restart NEXINT to try again.")
        return

    # -------------------------------------------------
    # 🛠️ ADMIN PANEL MENU
    # -------------------------------------------------
    while True:
        print("\n[ADMIN PANEL]")
        print("1. System status & statistics")
        print("2. Reload FAISS indices")
        print("3. Rebuild FAISS indices (DANGEROUS)")
        print("4. Integrity check")
        print("5. Export OSINT DB snapshot")
        print("6. Supervisor: WIPE ALL DATA (DANGEROUS)")
        print("0. Exit admin panel")

        choice = input("Select option: ").strip()

        try:
            if choice == "1":
                s = shared.admin_system_status()
                print("\n[SYSTEM STATUS]")
                print(f"Total records: {s['total_records']}")
                print("By type:")
                for k, v in s["by_type"].items():
                    print(f"  - {k}: {v}")
                print("FAISS:")
                for k, v in s["faiss"].items():
                    print(f"  - {k}: {v}")

            elif choice == "2":
                r = shared.admin_reload_indices()
                print(f"[OK] {r['message']}")

            elif choice == "3":
                print("⚠️ WARNING: This will rebuild all FAISS indices.")
                confirm = input("Type YES to confirm: ").strip()
                if confirm != "YES":
                    print("[INFO] Rebuild cancelled.")
                    continue
                r = shared.admin_rebuild_indices(confirm=True)
                print(f"[OK] {r['message']}")

            elif choice == "4":
                r = shared.admin_integrity_check()
                if r["status"] == "OK":
                    print("[OK] No integrity issues found.")
                else:
                    print("[ISSUES]")
                    for i in r["issues"]:
                        print(f" - {i}")

            elif choice == "5":
                path = input("Export file path (e.g. osint_snapshot.json): ").strip()
                r = shared.admin_export_osint_snapshot(path)
                print(f"[OK] Exported {r['records']} records to {r['exported_to']}")

            elif choice == "6":
                print("\n🔥🔥🔥 SUPERVISOR WIPE 🔥🔥🔥")
                print("THIS WILL PERMANENTLY DELETE ALL NEXINT DATA.")
                print("NO RECOVERY. NO UNDO.\n")

                step1 = input("Type SUPERVISOR to continue: ").strip()
                if step1 != "SUPERVISOR":
                    print("[ABORTED] Supervisor mode not entered.")
                    continue

                print("\nFinal confirmation required.")
                print("Type exactly:")
                print("DELETE ALL NEXINT DATA\n")

                phrase = input("Confirmation phrase: ").strip()
                final = input("Type YES DELETE EVERYTHING to proceed: ").strip()

                if final != "YES DELETE EVERYTHING":
                    print("[ABORTED] Final confirmation failed.")
                    continue

                try:
                    result = shared.supervisor_wipe_all(phrase)

                    print("\n💀 ALL DATA DESTROYED 💀")
                    for p in result.get("deleted", []):
                        print(f" - {p}")

                    print("\nSystem will now exit.")
                    print("Restart NEXINT to initialize a fresh environment.")
                    exit(0)

                except Exception as e:
                    print(f"[SUPERVISOR ERROR] {e}")

            elif choice == "0":
                break

            else:
                print("[ERROR] Invalid option.")

        except Exception as e:
            print(f"[ADMIN ERROR] {e}")



def forced_spinner(message="Initializing", duration=10):
    spinner = ['|', '/', '-', '\\']
    start = time.time()
    idx = 0

    while time.time() - start < duration:
        sys.stdout.write(f"\r{message}... {spinner[idx % len(spinner)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)

    # clear line after done
    sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
    sys.stdout.flush()



# -----------------------------------------------------
# MAIN MENU
# -----------------------------------------------------
def main_ui():
    while True:

        print(YELLOW + BOLD + "\nSelect a function:" + RESET)
        print("\n")
        print("1. Scan Image")
        print("2. Scan Video")
        print("3. Scan Git Repository")
        print("4. Scan Audio")
        print("5. Scan Text File (.txt)")
        print("6. enroll faces")
        print("7. Advanced Investigative Scan (image)")
        print("8. Advanced Investigative Scan (Video)")
        print("9. identity correlation")
        print("10. person timeline")
        print("11. exposure graph")
        print("12. sementic search")
        print("13. global search")
        print("14. report generator")
        print("15. admin panel")
        print("16. Exit")
        print(CYAN + BOLD + "run command= --help ( to demonstrate how to use )" + RESET)
        print("\n")
        choice = input("Enter choice: ").strip()

        if not choice:
            continue   # Ignore empty buffered input

        if choice == "1":
            scan_image_ui()
        elif choice == "2":
            scan_video_ui()
        elif choice == "3":
            scan_git_ui()
        elif choice == "4":
            scan_audio_ui()
        elif choice == "5":
            scan_text_ui()
        elif choice == "6":
            enroll_face_ui()
        elif choice == "7":
            scan_image_advanced_ui()
        elif choice == "8":
            scan_video_advanced_ui()
        elif choice == "9":
            identity_correlation_ui()
        elif choice == "10":
            person_timeline_ui()
        elif choice == "11":
            exposure_graph_ui()
        elif choice == "12":
            semantic_search_ui()
        elif choice == "13":
            global_search_ui()
        elif choice == "14":
            generate_report_ui()
        elif choice == "15":
            admin_panel_ui()
        elif choice == "16":
            forced_spinner(" -   closing PS1 OSINT Framework", duration=5)
            print("[INFO] Exiting...")
            break
        elif choice == "--help":
            main_help()
            return
        else:
            print("[ERROR] Invalid choice.")


# -----------------------------------------------------
# PROGRAM ENTRY
# -----------------------------------------------------
if __name__ == "__main__":
    forced_spinner(" -   initializing modules :", duration=4)
    startup()
    forced_spinner(" -   loading models : ",duration=4)
    forced_spinner(" -   starting PS1 OSINT Framework", duration=4)
    load_identities()
    save_identities()
    bootstrap()
    
    ban=random.randint(1,6)
    if ban == 1:
        banner1()
    elif ban == 2:
        banner2()
    elif ban == 3:
        banner3()
    elif ban == 4:
        banner4()
    elif ban == 5:
        banner5()
    elif ban == 6:
        banner6()
    else:
        pass
        
    banner()
    print( YELLOW + BOLD + "<< ⚠️  CAUTION ! DO NOT USE ON UNAUTHERISED NETWORKS OR SYSTEMS >>" + RESET)
    main_ui()








