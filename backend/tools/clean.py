

import os
import json

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data")
)

OSINT_DB_PATH = os.path.join(DATA_DIR, "osint_records.json")
META_DIR = os.path.join(DATA_DIR, "media_metadata")


def scan_osint_duplicates(records):
    seen = {}
    unique = []
    removed = 0

    for r in records:
        key = (r.get("type"), r.get("source"))
        if key in seen:
            removed += 1
            continue
        seen[key] = True
        unique.append(r)

    return unique, removed


def scan_faiss_duplicates(faiss_mgr):
    seen_hashes = {}
    to_remove = []

    for uid, meta in faiss_mgr.metadata.items():
        h = meta.get("file_hash")
        if not h:
            continue

        if h in seen_hashes:
            to_remove.append(uid)
        else:
            seen_hashes[h] = uid

    return to_remove


def remove_orphan_metadata(osint_sources, metadata_dir):
    removed = 0
    for root, _, files in os.walk(metadata_dir):
        for f in files:
            path = os.path.join(root, f)
            with open(path) as fh:
                meta = json.load(fh)

            if meta.get("source") not in osint_sources:
                os.remove(path)
                removed += 1

    return removed


# -------------------------------------------------
# ✅ REAL AUTO CLEANUP (SAFE)
# -------------------------------------------------

def auto_clean():
    """
    Automatic startup cleanup.
    Removes duplicates & orphans safely.
    """
    try:
        # 1️⃣ Load OSINT records
        if not os.path.exists(OSINT_DB_PATH):
            return

        with open(OSINT_DB_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not isinstance(records, list):
            return

        # 2️⃣ Remove OSINT duplicates
        cleaned, removed_osint = scan_osint_duplicates(records)

        if removed_osint > 0:
            with open(OSINT_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, indent=2)

        # Collect valid sources
        osint_sources = {
            r.get("source") for r in cleaned if r.get("source")
        }

        # 3️⃣ Remove orphan metadata
        remove_orphan_metadata(osint_sources, META_DIR)

        # 4️⃣ Clean FAISS duplicates (IF available)
        try:
            from backend.app.faiss_registry import vision_faiss, text_faiss, face_faiss

            for mgr in (vision_faiss, text_faiss, face_faiss):
                uids = scan_faiss_duplicates(mgr)
                for uid in uids:
                    mgr.delete(uid)  # must exist in your FaissManager
        except Exception:
            pass

    except Exception:
        # Never break startup
        return



'''def scan_osint_duplicates(records):
    seen = {}
    unique = []
    removed = 0

    for r in records:
        key = (r.get("type"), r.get("source"))
        if key in seen:
            removed += 1
            continue
        seen[key] = True
        unique.append(r)

    return unique, removed


def scan_faiss_duplicates(faiss_mgr):
    seen_hashes = {}
    to_remove = []

    for uid, meta in faiss_mgr.metadata.items():
        h = meta.get("file_hash")
        if not h:
            continue

        if h in seen_hashes:
            to_remove.append(uid)
        else:
            seen_hashes[h] = uid

    return to_remove


def remove_orphan_metadata(osint_sources, metadata_dir):
    removed = 0
    for root, _, files in os.walk(metadata_dir):
        for f in files:
            path = os.path.join(root, f)
            with open(path) as fh:
                meta = json.load(fh)

            if meta.get("source") not in osint_sources:
                os.remove(path)
                removed += 1

    return removed
'''
