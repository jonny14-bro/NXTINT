# backend/ai/intelligence_builder.py
import json
import os
from backend.app.ingest import compute_text_embedding
from backend.app.faiss_registry import text_faiss, vision_faiss, face_faiss
from shared import save_text_faiss_index

from backend.app.ingest import compute_text_embedding
from backend.ai.semantic_engine import semantic_faiss

from backend.ai.semantic_normalizer import (
    normalize_osint_record,
    normalize_media_metadata
)



def index_document(text, source, dtype):
    emb = compute_text_embedding(text)
    if emb:
        semantic_faiss.add(
            emb,
            metadata={
                "source": source,
                "type": dtype,
                "content": text
            }
        )


def rebuild_from_osint(osint_db_path):
    import json, os

    if not os.path.exists(osint_db_path):
        print("[AI] No OSINT DB found.")
        return

    with open(osint_db_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    added = 0

    for rec in records:
        text = normalize_osint_record(rec)
        emb = compute_text_embedding(text)

        if emb and len(emb) == text_faiss.dim:
            text_faiss.add(
                emb,
                metadata={
                    "type": rec.get("type"),
                    "source": rec.get("source"),
                    "normalized": text
                }
            )
            added += 1

    if save_text_faiss_index:
        save_text_faiss_index()

    print(f"[AI] Indexed {added} normalized OSINT records.")


def index_media_metadata(metadata_dir):
    indexed = 0

    for root, _, files in os.walk(metadata_dir):
        for f in files:
            if not f.endswith(".json"):
                continue

            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                continue

            semantic_text = json.dumps(data, ensure_ascii=False)
            emb = compute_text_embedding(semantic_text)

            if emb and len(emb) == text_faiss.dim:
                text_faiss.add(
                    emb,
                    metadata={
                        "type": "media_metadata",
                        "source": data.get("source"),
                        "content": data
                    }
                )
                indexed += 1

    if save_text_faiss_index:
        save_text_faiss_index()

    print(f"[AI] Indexed {indexed} media metadata documents.")




def rebuild_from_media_metadata(metadata_dir):
    import os, json

    indexed = 0

    for root, _, files in os.walk(metadata_dir):
        for f in files:
            if not f.endswith(".json"):
                continue

            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as fh:
                meta = json.load(fh)

            text = normalize_media_metadata(meta)
            emb = compute_text_embedding(text)

            if emb and len(emb) == text_faiss.dim:
                text_faiss.add(
                    emb,
                    metadata={
                        "type": "media_metadata",
                        "source": meta.get("source"),
                        "normalized": text
                    }
                )
                indexed += 1

    if save_text_faiss_index:
        save_text_faiss_index()

    print(f"[AI] Indexed {indexed} media metadata intelligence units.")



