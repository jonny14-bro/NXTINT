# shared.py
from curses import meta
import os
import uuid
import json
import tempfile
import shutil
import hashlib
import hmac
import secrets
import re
import numpy as np
from datetime import datetime
from collections import defaultdict

from backend.app.ingest import extract_exif, compute_image_embedding
from backend.app.faiss_manager import FaissManager

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



# -----------------------------------------------------
# SHARED STATE (Injected at runtime)
# -----------------------------------------------------
faiss_manager: FaissManager = None
append_osint_record = None
save_faiss_index = None

# -----------------------------------------------------
# TEXT DETECTION (DETERMINISTIC LAYER)
# -----------------------------------------------------

SECRET_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\+?\d[\d\s\-]{8,}\d"),
    "api_key": re.compile(r"(api[_-]?key\s*=\s*[\"']?.+?[\"']?)", re.I),
    "password": re.compile(r"(password\s*=\s*[\"']?.+?[\"']?)", re.I),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
    "private_key": re.compile(r"-----BEGIN (RSA|EC|DSA) PRIVATE KEY-----"),
    "base64": re.compile(r"\b[A-Za-z0-9+/=]{20,}\b"),
}

# -----------------------------------------------------
# HYBRID TEXT QUERY (DETECTION + SEMANTIC)
# -----------------------------------------------------

def hybrid_text_query(query: str, top_k: int = 5):
    """
    Query-aware intelligence analysis:
    - Detection for secrets / identifiers
    - Semantic search only for context
    """

    records = _load_osint_db()
    text_records = [
        r for r in records
        if r.get("type") == "text" and r.get("source")
    ]

    detections = []
    semantic_results = []

    # --- Detection phase ---
    for r in text_records:
        try:
            with open(r["source"], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        found = detect_sensitive_entities(content)

        if found:
            detections.append({
                "source": r["source"],
                "length": len(content),
                "findings": found
            })

    # --- If query is detection-oriented, STOP here ---
    trigger_words = [
        "secret", "password", "key", "email",
        "token", "credential", "admin"
    ]

    if any(w in query.lower() for w in trigger_words):
        return {
            "mode": "DETECTION",
            "detections": detections
        }

    # --- Semantic phase (only if needed) ---
    embedding = compute_text_embedding(query)
    if embedding and len(embedding) == text_faiss.dim:
        semantic_results = text_faiss.search_by_vector(
            embedding, k=top_k
        )

    return {
        "mode": "SEMANTIC",
        "results": semantic_results
    }


def detect_sensitive_entities(text: str) -> dict:
    findings = {}

    for name, pattern in SECRET_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            findings[name] = list(set(matches))

    return findings

def configure(
    *,
    faiss_mgr: FaissManager,
    append_record_fn,
    save_faiss_fn
):
    """
    Dependency injection.
    UI / main decides WHAT implementations to use.
    """
    global faiss_manager, append_osint_record, save_faiss_index
    faiss_manager = faiss_mgr
    append_osint_record = append_record_fn
    save_faiss_index = save_faiss_fn

def _load_faiss_index():
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        try:
            faiss_manager.load(INDEX_PATH, META_PATH)
            print(f"[INFO] Loaded image/video FAISS index with {faiss_manager.count()} items.")
        except Exception as e:
            print(f"[WARN] Could not load FAISS index: {e}")
    else:
        print("[INFO] No existing image/video FAISS index found.")

def _load_face_faiss():
    if os.path.exists(FACE_INDEX_PATH) and os.path.exists(FACE_META_PATH):
        try:
            face_faiss.load(FACE_INDEX_PATH, FACE_META_PATH)
            print(f"[INFO] Loaded face FAISS with {face_faiss.count()} faces.")
        except Exception as e:
            print(f"[WARN] Could not load face FAISS: {e}")

def _load_text_faiss_index():
    if os.path.exists(TEXT_INDEX_PATH) and os.path.exists(TEXT_META_PATH):
        try:
            text_faiss.load(TEXT_INDEX_PATH, TEXT_META_PATH)
            print(f"[INFO] Loaded text FAISS index with {text_faiss.count()} items.")
        except Exception as e:
            print(f"[WARN] Could not load text FAISS index: {e}")
    else:
        print("[INFO] No existing text FAISS index found; starting empty.")

def _save_face_faiss():
    try:
        face_faiss.save(FACE_INDEX_PATH, FACE_META_PATH)
    except Exception as e:
        print(f"[WARN] Failed to save face FAISS: {e}")

def _load_osint_db():
    if not os.path.exists(OSINT_DB_PATH):
        return []
    try:
        with open(OSINT_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _append_osint_record(record: dict):
    records = _load_osint_db()
    records.append(record)
    _save_osint_db(records)

def _save_osint_db(records):
    try:
        with open(OSINT_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=4)
    except Exception as e:
        print(f"[WARN] Failed to save OSINT DB: {e}")


# -----------------------------------------------------
# face similarity match result
# -----------------------------------------------------

def identify_face(matches, threshold=0.6):
    """
    OLD LOGIC (RESTORED)

    matches: list of (uid, similarity, metadata)
    similarity is assumed to be cosine similarity (0 → 1)
    """

    if not matches:
        return "UNKNOWN", 0.0, None

    uid, sim, meta = matches[0]

    confidence = round(sim * 100, 2)

    if confidence < threshold * 100:
        return "UNKNOWN", confidence, None
    label = (
        meta.get("identity") or "UNKNOWN"
    )


    '''label = (
        meta.get("label")
        or meta.get("identity")
        or meta.get("source")
        or "KNOWN_FACE"
    )'''
    return label, confidence, uid

# -----------------------------------------------------
# CORE IMAGE SCAN (ENGINE)
# -----------------------------------------------------
def scan_image(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("File does not exist")

    exif = extract_exif(path)

    # sanitize thumbnail if present
    if (
        isinstance(exif, dict)
        and "piexif" in exif
        and isinstance(exif["piexif"], dict)
        and "thumbnail" in exif["piexif"]
    ):
        exif["piexif"]["thumbnail"] = "[REMOVED]"

    embedding = compute_image_embedding(path)
    embedding_len = len(embedding) if embedding else 0

    uid = None
    if embedding and embedding_len == faiss_manager.dim:
        uid = faiss_manager.add(
            embedding,
            metadata={
                "type": "image",
                "filename": os.path.basename(path),
                "source": path,
                "exif_present": bool(exif.get("raw_exif"))
            }
        )
        save_faiss_index()

    matches = []
    if uid is not None:
        matches = faiss_manager.search_by_uid(uid, k=5)

    record = {
        "type": "image",
        "source": path,
        "filename": os.path.basename(path),
        "faiss_uid": uid,
        "exif": exif,
        "embedding_len": embedding_len,
    }
    append_osint_record(record)

    return {
        "filename": os.path.basename(path),
        "exif": exif,
        "embedding_len": embedding_len,
        "faiss_uid": uid,
        "matches": matches,
    }




# shared.py (scan_video)

import tempfile
import shutil

from backend.app.ingest import (
    extract_frames,
    process_image_faces,
    save_best_identity_frame,
)
from backend.app.faiss_registry import face_faiss


def scan_video(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("File does not exist")

    tmpdir = tempfile.mkdtemp(prefix="frames_")

    frames = extract_frames(path, out_dir=tmpdir, every_n=15)
    if not frames:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return {
            "frames": [],
            "faces": [],
            "message": "No frames extracted"
        }

    frame_results = []
    face_results = []

    for frame_path in frames:
        embedding = compute_image_embedding(frame_path)

        uid = None
        if embedding and len(embedding) == faiss_manager.dim:
            uid = faiss_manager.add(
                embedding,
                metadata={
                    "type": "video_frame",
                    "frame": os.path.basename(frame_path),
                    "source": path
                }
            )

        frame_results.append({
            "frame": frame_path,
            "faiss_uid": uid
        })

        # -------- FACE PROCESSING --------
        faces = process_image_faces(frame_path, conf_thresh=0.30)

        for face in faces:
            emb = face.get("embedding")
            bbox = face.get("bbox")

            if not emb or len(emb) != face_faiss.dim:
                continue

            uid_face = face_faiss.add_face(
                emb,
                source=path,
                bbox=bbox,
                identity=None
            )

            save_best_identity_frame(
                uid_face,
                frame_path,
                bbox
            )

            face_results.append({
                "frame": frame_path,
                "bbox": bbox,
                "face_uid": uid_face
            })

    save_faiss_index()

    record = {
        "type": "video",
        "source": path,
        "frames": len(frame_results),
        "faces": len(face_results),
    }
    append_osint_record(record)

    shutil.rmtree(tmpdir, ignore_errors=True)

    return {
        "frames": frame_results,
        "faces": face_results
    }


# shared.py (GIT SCAN)


from backend.app.ingest import scan_git_repo_for_secrets_with_reports


def scan_git_repo(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Repository path does not exist")

    if not os.path.isdir(path):
        raise ValueError("Provided path is not a directory")

    report = scan_git_repo_for_secrets_with_reports(path)

    # Safe extraction (based on actual ingest output)
    raw_findings = report.get("raw_findings", [])
    clean_report = report.get("clean_report", [])
    timestamp = report.get("timestamp")

    total_findings = len(raw_findings)

    record = {
        "type": "git",
        "source": path,
        "findings": total_findings,
        "timestamp": timestamp,
    }

    append_osint_record(record)

    return {
        "path": path,
        "total_findings": total_findings,
        "raw_findings": raw_findings,
        "clean_report": clean_report,
        "timestamp": timestamp,
        "raw_report": report,
    }


# shared.py ( scan_text )

from backend.app.ingest import compute_text_embedding


# injected at configure()
text_faiss = None
save_text_faiss_index = None


def configure_text(
    *,
    text_faiss_mgr,
    save_text_faiss_fn
):
    global text_faiss, save_text_faiss_index
    text_faiss = text_faiss_mgr
    save_text_faiss_index = save_text_faiss_fn


def scan_text(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Text file does not exist")

    if not os.path.isfile(path):
        raise ValueError("Provided path is not a file")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if not content.strip():
        raise ValueError("Text file is empty")

    embedding = compute_text_embedding(content)

    uid = None
    if embedding and len(embedding) == text_faiss.dim:
        uid = text_faiss.add(
            embedding,
            metadata={
                "type": "text",
                "source": path,
                "length": len(content),
            }
        )
        save_text_faiss_index()

    record = {
        "type": "text",
        "source": path,
    }
    append_osint_record({
        "type": "text",
        "source": path,
        "length": len(content),
        "faiss_uid": uid,
    })

    return {
        "path": path,
        "length": len(content),
        "faiss_uid": uid,
    }




# shared.py (scan_audio)

from backend.app.ingest import analyze_audio


def scan_audio(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Audio file does not exist")

    if not os.path.isfile(path):
        raise ValueError("Provided path is not a file")

    analysis = analyze_audio(path)

    record = {
        "type": "audio",
        "source": path,
        "duration": analysis.get("duration"),
        "codec": analysis.get("codec"),
        "sample_rate": analysis.get("sample_rate"),
        "channels": analysis.get("channels"),
    }

    append_osint_record(record)

    return {
        "path": path,
        "analysis": analysis
    }




# shared.py (ADVANCED IMAGE SCAN)

from backend.app.ingest import process_image_faces
from backend.app.faiss_registry import face_faiss
from backend.app.ingest import save_best_identity_frame


from core.audit import audit
from core.schema import require_keys, clamp_confidence

def scan_image_advanced(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Image file does not exist")

    # --- Step 1: Base image scan (non-destructive) ---
    base = scan_image(path)

    intelligence_notes = []
    faces_report = []

    # --- Step 2: Face detection ---
    faces = process_image_faces(path, conf_thresh=0.30)

    if not faces:
        intelligence_notes.append("No faces detected in image.")
    else:
        intelligence_notes.append(f"{len(faces)} face(s) detected.")

    # Ensure deterministic order (S8)
    faces = sorted(faces, key=lambda f: str(f.get("bbox")))

    for face in faces:
        emb = face.get("embedding")
        bbox = face.get("bbox")

        if not emb or len(emb) != face_faiss.dim:
            continue

        # --- Normalize (deterministic) ---
        vec = np.asarray(emb, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm == 0:
            continue
        vec /= norm

        # --- Similarity search ---
        matches = face_faiss.search_by_vector(vec.tolist(), k=5)

        # Remove self-matches
        matches = [
            (uid, sim, meta)
            for uid, sim, meta in matches
            if meta and meta.get("source") != path
        ]

        # --- Identity inference ---
        label, confidence, _ = identify_face(matches)
        confidence = clamp_confidence(confidence)

        faces_report.append({
            "bbox": bbox,
            "identity": label,
            "confidence": confidence,
            "matches": matches,
        })

        # --- Persist identity evidence (CRITICAL FIX) ---
        if label != "UNKNOWN" and confidence >= 60:
            _append_osint_record({
                "type": "identity_evidence",
                "identity": label,
                "source": path,
                "frames_seen": 1,
                "avg_confidence": confidence,
                "bbox": bbox,
                "timestamp": datetime.utcnow().isoformat()
            })

            intelligence_notes.append(
                f"Identity evidence recorded for {label} ({confidence}%)."
            )

        # --- Persist face embedding (unchanged logic) ---
        store_identity = None
        if label != "UNKNOWN" and confidence >= 70:
            store_identity = label
            intelligence_notes.append(
                f"Face identified as {label} with {confidence}% confidence."
            )

        uid = face_faiss.add_face(
            emb,
            source=path,
            bbox=bbox,
            identity=store_identity
        )

        save_best_identity_frame(uid, path, bbox)

    _save_face_faiss()

    record = {
        "type": "image_advanced",
        "source": path,
        "faces_detected": len(faces_report),
        "timestamp": datetime.utcnow().isoformat()
    }

    # --- Schema guard (S8) ---
    require_keys(
        record,
        ["type", "source", "faces_detected", "timestamp"],
        ctx="image_advanced"
    )

    # --- OSINT record ---
    _append_osint_record(record)

    # --- Cryptographic audit ---
    _append_osint_record(
        audit("image_advanced", record)
    )

    result = {
        "image": base,
        "faces": faces_report,
        "intelligence_notes": intelligence_notes,
    }

    # --- Output schema guarantee ---
    require_keys(
        result,
        ["image", "faces", "intelligence_notes"],
        ctx="image_advanced_output"
    )

    return result


'''
def scan_image_advanced(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Image file does not exist")

    # --- Step 1: Base image scan (non-destructive) ---
    base = scan_image(path)

    intelligence_notes = []
    faces_report = []

    # --- Step 2: Face detection ---
    faces = process_image_faces(path, conf_thresh=0.30)

    if not faces:
        intelligence_notes.append("No faces detected in image.")
    else:
        intelligence_notes.append(f"{len(faces)} face(s) detected.")

    # Ensure deterministic order (S8)
    faces = sorted(
        faces,
        key=lambda f: str(f.get("bbox"))
    )

    for face in faces:
        emb = face.get("embedding")
        bbox = face.get("bbox")

        if not emb or len(emb) != face_faiss.dim:
            continue

        # --- Normalize (deterministic) ---
        vec = np.asarray(emb, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm == 0:
            continue
        vec = vec / norm

        # --- Similarity search ---
        matches = face_faiss.search_by_vector(vec.tolist(), k=5)

        # Remove self-matches
        matches = [
            (uid, sim, meta)
            for uid, sim, meta in matches
            if meta and meta.get("source") != path
        ]

        # --- Identity inference ---
        label, confidence, _ = identify_face(matches)
        confidence = clamp_confidence(confidence)

        faces_report.append({
            "bbox": bbox,
            "identity": label,
            "confidence": confidence,
            "matches": matches,
        })

        # --- Persist face embedding ---
        store_identity = None
        if label != "UNKNOWN" and confidence >= 70:
            store_identity = label
            intelligence_notes.append(
                f"Face identified as {label} with {confidence}% confidence."
            )

        uid = face_faiss.add_face(
            emb,
            source=path,
            bbox=bbox,
            identity=store_identity
        )

        save_best_identity_frame(uid, path, bbox)

    _save_face_faiss()

    record = {
        "type": "image_advanced",
        "source": path,
        "faces_detected": len(faces_report),
        "timestamp": datetime.utcnow().isoformat()
    }

    # --- Schema guard (S8) ---
    require_keys(
        record,
        ["type", "source", "faces_detected", "timestamp"],
        ctx="image_advanced"
    )

    # --- OSINT record ---
    _append_osint_record(record)

    # --- Cryptographic audit ---
    _append_osint_record(
        audit("image_advanced", record)
    )

    result = {
        "image": base,
        "faces": faces_report,
        "intelligence_notes": intelligence_notes,
    }

    # --- Output schema guarantee ---
    require_keys(
        result,
        ["image", "faces", "intelligence_notes"],
        ctx="image_advanced_output"
    )

    return result

'''


# shared.py (ADVANCED VIDEO SCAN)

from backend.app.ingest import extract_frames, process_image_faces
from backend.app.faiss_registry import face_faiss
from backend.app.ingest import save_best_identity_frame


from core.audit import audit
from core.schema import require_keys, clamp_confidence

def scan_video_advanced(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Video file does not exist")

    tmpdir = tempfile.mkdtemp(prefix="adv_frames_")

    try:
        frames = extract_frames(path, out_dir=tmpdir, fps=5)
        if not frames:
            return {"error": "No frames extracted"}

        frames = sorted(frames)

        identity_hits = defaultdict(list)
        face_count = 0

        for frame in frames:
            faces = process_image_faces(frame, conf_thresh=0.25)

            for face in faces:
                emb = face.get("embedding")
                bbox = face.get("bbox")

                if not emb or len(emb) != face_faiss.dim:
                    continue

                # 🔒 deterministic normalization
                vec = np.asarray(emb, dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm == 0:
                    continue
                vec /= norm

                # 🔍 read-only FAISS search
                matches = face_faiss.search_by_vector(vec.tolist(), k=5)

                # ✅ ONLY enrolled identities
                matches = [
                    (uid, sim, meta)
                    for uid, sim, meta in matches
                    if meta and meta.get("enrolled") is True
                ]

                label, confidence, _ = identify_face(matches)
                confidence = clamp_confidence(confidence)

                face_count += 1

                if label != "UNKNOWN":
                    identity_hits[label].append({
                        "confidence": confidence,
                        "frame": os.path.basename(frame),
                        "bbox": bbox
                    })

        # ⏱ TEMPORAL CONFIRMATION
        MIN_FRAMES = 3
        identities = []
        intelligence_notes = []

        for identity, hits in identity_hits.items():
            if len(hits) < MIN_FRAMES:
                continue

            avg_conf = round(
                sum(h["confidence"] for h in hits) / len(hits), 2
            )

            best = max(hits, key=lambda x: x["confidence"])

            identity_entry = {
                "identity": identity,
                "avg_confidence": clamp_confidence(avg_conf),
                "frames_seen": len(hits),
                "best_frame": best["frame"]
            }

            identities.append(identity_entry)

            intelligence_notes.append(
                f"{identity} confirmed in {len(hits)} frames"
            )

            # 🧠 🔑 CRITICAL FIX: persist identity evidence
            _append_osint_record({
                "type": "identity_evidence",
                "identity": identity,
                "source": path,
                "frames_seen": len(hits),
                "avg_confidence": identity_entry["avg_confidence"],
                "best_frame": best["frame"],
                "timestamp": datetime.utcnow().isoformat()
            })

        # 📁 main OSINT record
        record = {
            "type": "video_advanced",
            "source": path,
            "frames_processed": len(frames),
            "faces_detected": face_count,
            "identities": identities,
            "timestamp": datetime.utcnow().isoformat()
        }

        require_keys(
            record,
            [
                "type",
                "source",
                "frames_processed",
                "faces_detected",
                "identities",
                "timestamp"
            ],
            ctx="video_advanced"
        )

        _append_osint_record(record)
        _append_osint_record(audit("video_advanced", record))

        return {
            "video": path,
            "frames_processed": len(frames),
            "faces_detected": face_count,
            "identities": identities,
            "intelligence_notes": intelligence_notes
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


'''
def scan_video_advanced(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Video file does not exist")

    tmpdir = tempfile.mkdtemp(prefix="adv_frames_")

    try:
        frames = extract_frames(path, out_dir=tmpdir, fps=5)
        if not frames:
            return {"error": "No frames extracted"}

        frames = sorted(frames)

        identity_hits = defaultdict(list)
        face_count = 0

        for frame in frames:
            faces = process_image_faces(frame, conf_thresh=0.25)

            for face in faces:
                emb = face.get("embedding")
                bbox = face.get("bbox")

                if not emb or len(emb) != face_faiss.dim:
                    continue

                # 🔒 EXACT SAME normalization as enrollment
                vec = np.asarray(emb, dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm == 0:
                    continue
                vec /= norm

                # 🔍 READ-ONLY search
                matches = face_faiss.search_by_vector(vec.tolist(), k=5)

                # ✅ ONLY enrolled identities
                matches = [
                    (uid, sim, meta)
                    for uid, sim, meta in matches
                    if meta and meta.get("enrolled") is True
                ]

                label, confidence, _ = identify_face(matches)
                confidence = clamp_confidence(confidence)

                face_count += 1

                if label != "UNKNOWN":
                    identity_hits[label].append({
                        "confidence": confidence,
                        "frame": os.path.basename(frame),
                        "bbox": bbox
                    })

        # ⏱ TEMPORAL CONFIRMATION
        MIN_FRAMES = 3
        identities = []
        intelligence_notes = []

        for identity, hits in identity_hits.items():
            if len(hits) < MIN_FRAMES:
                continue

            avg_conf = round(
                sum(h["confidence"] for h in hits) / len(hits), 2
            )

            best = max(hits, key=lambda x: x["confidence"])

            identities.append({
                "identity": identity,
                "avg_confidence": clamp_confidence(avg_conf),
                "frames_seen": len(hits),
                "best_frame": best["frame"]   # ✅ FIXED
            })

            intelligence_notes.append(
                f"{identity} confirmed in {len(hits)} frames"
            )

        record = {
            "type": "video_advanced",
            "source": path,
            "frames_processed": len(frames),
            "faces_detected": face_count,
            "identities": identities,
            "timestamp": datetime.utcnow().isoformat()
        }

        require_keys(
            record,
            [
                "type",
                "source",
                "frames_processed",
                "faces_detected",
                "identities",
                "timestamp"
            ],
            ctx="video_advanced"
        )

        _append_osint_record(record)
        _append_osint_record(audit("video_advanced", record))

        return {
            "video": path,
            "frames_processed": len(frames),
            "faces_detected": face_count,
            "identities": identities,
            "intelligence_notes": intelligence_notes
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

        
        '''



# shared.py (FACE ENROLLMENT)

from backend.app.ingest import process_image_faces, save_best_identity_frame
from backend.app.faiss_registry import face_faiss


from core.audit import audit
from core.schema import require_keys




def enroll_face(path: str, identity: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError("Image file does not exist")

    if not identity or not identity.strip():
        raise ValueError("Identity name cannot be empty")

    faces = process_image_faces(path, conf_thresh=0.35)

    if not faces:
        raise ValueError("No face detected in image")

    if len(faces) > 1:
        raise ValueError("Multiple faces detected. Enrollment requires exactly one face.")

    face = faces[0]
    emb = face.get("embedding")
    bbox = face.get("bbox")

    if not emb or len(emb) != face_faiss.dim:
        raise ValueError("Invalid face embedding")

    # --- Normalize (deterministic) ---
    vec = np.asarray(emb, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm == 0:
        raise ValueError("Invalid embedding vector")
    vec = vec / norm

    # --- FAISS insert (atomic intent) ---
    uid = face_faiss.add_face(
        vec.tolist(),
        source=path,
        bbox=bbox,
        identity=identity,
        enrolled=True
    )

    save_best_identity_frame(uid, path, bbox if isinstance(bbox, (list, tuple)) else list(bbox))
    _save_face_faiss()

    record = {
        "type": "face_enroll",
        "identity": identity,
        "source": path,
        "face_uid": uid,
        "enrolled": True,
        "timestamp": datetime.utcnow().isoformat()
    }

    # --- Schema guard ---
    require_keys(
        record,
        ["type", "identity", "source", "face_uid", "enrolled", "timestamp"],
        ctx="face_enroll"
    )

    # --- Append OSINT record ---
    _append_osint_record(record)

    # --- Cryptographic audit ---
    _append_osint_record(
        audit("face_enroll", record)
    )

    return {
        "identity": identity,
        "bbox": bbox,
        "uid": uid,
        "message": "Face successfully enrolled"
    }



# shared.py (IDENTITY CORRELATION)


from core.schema import require_keys, clamp_confidence
from core.audit import audit

def correlate_identity(identity: str) -> dict:
    if not identity or identity == "UNKNOWN":
        raise ValueError("Invalid identity name")

    records = _load_osint_db()

    # --- Enrollment truth ---
    enrolled = any(
        r.get("type") == "face_enroll" and r.get("identity") == identity
        for r in records
    )

    # --- Evidence from sightings (READ identity_evidence) ---
    evidence = []
    sources = defaultdict(int)
    timestamps = []

    for r in records:
        if r.get("type") != "identity_evidence":
            continue
        if r.get("identity") != identity:
            continue

        src = r.get("source")
        if src:
            sources[src] += 1

        ts = r.get("timestamp")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts))
            except Exception:
                pass

        evidence.append({
            "source": src,
            "frames_seen": r.get("frames_seen"),
            "avg_confidence": r.get("avg_confidence"),
        })

    if not evidence:
        return {
            "identity": identity,
            "status": "NO_EVIDENCE",
            "message": "Identity enrolled but not observed in external media."
        }

    # --- Deterministic confidence (unchanged logic) ---
    base_score = min(len(evidence) * 10, 60)
    diversity_bonus = min(len(sources) * 5, 20)
    enrollment_bonus = 20 if enrolled else 0

    confidence = clamp_confidence(
        base_score + diversity_bonus + enrollment_bonus
    )

    summary = {
        "identity": identity,
        "status": "OK",
        "confidence": confidence,
        "faces_detected": len(evidence),
        "unique_sources": len(sources),
        "enrolled": enrolled,
        "first_seen": min(timestamps).isoformat() if timestamps else None,
        "last_seen": max(timestamps).isoformat() if timestamps else None,
        "sources": sorted(sources.keys()),
        "evidence": evidence,
    }

    require_keys(
        summary,
        [
            "identity",
            "confidence",
            "faces_detected",
            "unique_sources",
            "enrolled",
            "sources",
            "evidence",
        ],
        ctx="identity_correlation"
    )

    # --- Audit only (unchanged) ---
    _append_osint_record({
        "type": "identity_correlation",
        "identity": identity,
        "confidence": confidence,
        "faces": len(evidence),
        "sources": sorted(sources.keys()),
        "timestamp": datetime.utcnow().isoformat()
    })

    _append_osint_record(
        audit("identity_correlation", summary)
    )

    return summary


'''
def correlate_identity(identity: str) -> dict:
    if not identity or identity == "UNKNOWN":
        raise ValueError("Invalid identity name")

    records = _load_osint_db()

    # --- Enrollment truth ---
    enrolled = any(
        r.get("type") == "face_enroll" and r.get("identity") == identity
        for r in records
    )

    # --- Evidence from sightings (NOT enrollment) ---
    evidence = []
    sources = defaultdict(int)
    timestamps = []

    for r in records:
        if r.get("identity") != identity:
            continue

        if r.get("type") not in {"video_advanced", "image_advanced"}:
            continue

        src = r.get("source")
        if src:
            sources[src] += 1

        ts = r.get("timestamp")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts))
            except Exception:
                pass

        evidence.append({
            "source": src,
            "bbox": r.get("bbox"),
        })

    if not evidence:
        return {
            "identity": identity,
            "status": "NO_EVIDENCE",
            "message": "Identity enrolled but not observed in external media."
        }

    # --- Deterministic confidence ---
    base_score = min(len(evidence) * 10, 60)
    diversity_bonus = min(len(sources) * 5, 20)
    enrollment_bonus = 20 if enrolled else 0

    confidence = clamp_confidence(
        base_score + diversity_bonus + enrollment_bonus
    )

    summary = {
        "identity": identity,
        "confidence": confidence,
        "faces_detected": len(evidence),
        "unique_sources": len(sources),
        "enrolled": enrolled,
        "first_seen": min(timestamps).isoformat() if timestamps else None,
        "last_seen": max(timestamps).isoformat() if timestamps else None,
        "sources": sorted(sources.keys()),
        "evidence": evidence,
    }

    require_keys(
        summary,
        [
            "identity",
            "confidence",
            "faces_detected",
            "unique_sources",
            "enrolled",
            "sources",
            "evidence",
        ],
        ctx="identity_correlation"
    )

    _append_osint_record({
        "type": "identity_correlation",
        "identity": identity,
        "confidence": confidence,
        "faces": len(evidence),
        "sources": sorted(sources.keys()),
        "timestamp": datetime.utcnow().isoformat()
    })

    _append_osint_record(
        audit("identity_correlation", summary)
    )

    return summary

'''


# shared.py (PERSON TIMELINE)


from core.schema import require_keys
from core.audit import audit

def build_person_timeline(identity: str) -> list:
    if not identity or identity == "UNKNOWN":
        raise ValueError("Invalid identity")

    records = _load_osint_db()
    timeline = []

    for r in records:
        # Safe identity presence check (S8)
        try:
            if identity not in json.dumps(r, default=str):
                continue
        except Exception:
            continue

        ts = (
            r.get("timestamp")
            or r.get("time")
            or r.get("created_at")
        )

        try:
            ts_obj = datetime.fromisoformat(ts) if ts else None
        except Exception:
            ts_obj = None

        entry = {
            "timestamp": ts,
            "event_type": r.get("type"),
            "source": r.get("source"),
            "description": None,
            "raw": r
        }

        et = r.get("type")

        if et == "face_enroll":
            entry["description"] = f"Identity '{identity}' enrolled from image."

        elif et == "image_advanced":
            entry["description"] = f"Advanced image scan detected '{identity}'."

        elif et == "video_advanced":
            entry["description"] = f"Advanced video analysis reinforced identity '{identity}'."

        elif et == "identity_correlation":
            conf = r.get("confidence")
            entry["description"] = (
                f"Identity correlation confidence updated to {conf}%."
            )

        else:
            entry["description"] = f"Related event detected for '{identity}'."

        # --- Schema guard per entry (S8) ---
        require_keys(
            entry,
            ["timestamp", "event_type", "source", "description", "raw"],
            ctx="person_timeline_entry"
        )

        timeline.append({
            **entry,
            "_ts_obj": ts_obj  # internal only
        })

    # Deterministic chronological sort (S8)
    timeline.sort(
        key=lambda x: (
            x["_ts_obj"] is None,
            x["_ts_obj"] or datetime.max,
            x["event_type"] or ""
        )
    )

    # Cleanup internal helpers
    for t in timeline:
        t.pop("_ts_obj", None)

    # --- Audit (read-only intelligence view) ---
    _append_osint_record(
        audit(
            "person_timeline_view",
            {
                "identity": identity,
                "entries": len(timeline)
            }
        )
    )

    return timeline


# shared.py (EXPOSURE GRAPH)


from core.schema import require_keys
from core.audit import audit

def build_exposure_graph(identity_filter: str | None = None) -> dict:
    records = _load_osint_db()

    graph = {
        "identities": set(),
        "sources": set(),
        "edges": defaultdict(set),  # node -> set(nodes)
    }

    # Cache known identities once (deterministic)
    known_identities = sorted(_extract_known_identities())

    for r in records:
        src = r.get("source")
        if not src:
            continue

        # Safe stringify for search (S8)
        try:
            raw = json.dumps(r, default=str)
        except Exception:
            raw = ""

        identities = set()

        # Direct identity fields
        if isinstance(r.get("identity"), str):
            identities.add(r.get("identity"))

        # Nested structures
        for key in ("identities", "faces", "identity"):
            val = r.get(key)
            if isinstance(val, list):
                for v in val:
                    if isinstance(v, dict) and isinstance(v.get("identity"), str):
                        identities.add(v["identity"])
            elif isinstance(val, str):
                identities.add(val)

        # Fallback text search against known identities
        for known in known_identities:
            if known and known in raw:
                identities.add(known)

        for identity in identities:
            if not identity or identity == "UNKNOWN":
                continue
            if identity_filter and identity != identity_filter:
                continue

            id_node = f"IDENTITY:{identity}"
            src_node = f"SOURCE:{src}"

            graph["identities"].add(id_node)
            graph["sources"].add(src_node)
            graph["edges"][id_node].add(src_node)
            graph["edges"][src_node].add(id_node)

    # Deterministic output (S8)
    result = {
        "identities": sorted(graph["identities"]),
        "sources": sorted(graph["sources"]),
        "edges": {
            k: sorted(v) for k, v in sorted(graph["edges"].items(), key=lambda x: x[0])
        }
    }

    # Schema guard (S8)
    require_keys(
        result,
        ["identities", "sources", "edges"],
        ctx="exposure_graph"
    )

    # Audit (read-only view)
    _append_osint_record(
        audit(
            "exposure_graph_view",
            {
                "identity_filter": identity_filter,
                "identities": len(result["identities"]),
                "sources": len(result["sources"]),
                "edges": sum(len(v) for v in result["edges"].values()),
            }
        )
    )

    return result


def _extract_known_identities():
    """
    Helper: returns known identity names from registry.
    """
    try:
        with open(FACE_IDENTITY_PATH, "r") as f:
            data = json.load(f)
            return list(data.get("identities", {}).keys())
    except Exception:
        return []



# shared.py (REPORT GENERATION)


from core.schema import require_keys, clamp_confidence
from core.audit import audit
import hashlib, json

def generate_identity_report(identity: str) -> dict:
    if not identity or identity == "UNKNOWN":
        raise ValueError("Invalid identity")

    # --- Pull intelligence (NO new inference) ---
    correlation = correlate_identity(identity)
    timeline = build_person_timeline(identity)
    exposure = build_exposure_graph(identity)

    if not correlation.get("evidence"):
        raise ValueError("Cannot generate report: no evidence available")

    report_id = f"NEXINT-REP-{uuid.uuid4().hex[:8].upper()}"

    # --- Clamp confidence defensively (S8) ---
    confidence = clamp_confidence(correlation.get("confidence", 0))

    # Deterministic ordering (S8)
    timeline = list(timeline)
    exposure["identities"] = sorted(exposure.get("identities", []))
    exposure["sources"] = sorted(exposure.get("sources", []))
    exposure["edges"] = {
        k: sorted(v) for k, v in exposure.get("edges", {}).items()
    }

    confidence_assessment = {
        "score": confidence,
        "level": (
            "HIGH" if confidence >= 80 else
            "MEDIUM" if confidence >= 50 else
            "LOW"
        ),
        "explanation": [
            f"{correlation['faces_detected']} face detections",
            f"{correlation['unique_sources']} unique sources",
            "Enrolled identity anchor present"
            if correlation["enrolled"] else
            "No enrollment anchor"
        ]
    }

    report = {
        "report_id": report_id,
        "generated_at": datetime.utcnow().isoformat(),
        "framework": "NEXINT v1",
        "scope": {
            "identity": identity
        },
        "summary": {
            "confidence": confidence,
            "faces_detected": correlation["faces_detected"],
            "unique_sources": correlation["unique_sources"],
            "first_seen": correlation.get("first_seen"),
            "last_seen": correlation.get("last_seen"),
        },
        "identity_profile": {
            "identity": identity,
            "enrolled": correlation["enrolled"],
            "sources": correlation["sources"],
        },
        "timeline": timeline,
        "exposure_graph": exposure,
        "evidence": correlation["evidence"],
        "confidence_assessment": confidence_assessment,
        "notes": [
            "This report is generated automatically by NEXINT v1.",
            "All conclusions are evidence-backed and explainable.",
            "No probabilistic inference beyond recorded confidence scores."
        ]
    }

    # --- Schema guard (S8) ---
    require_keys(
        report,
        [
            "report_id",
            "generated_at",
            "framework",
            "scope",
            "summary",
            "identity_profile",
            "timeline",
            "exposure_graph",
            "evidence",
            "confidence_assessment",
        ],
        ctx="identity_report"
    )

    # --- Immutable fingerprint (S8) ---
    report["fingerprint"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, default=str).encode()
    ).hexdigest()

    # --- OSINT record (report creation) ---
    _append_osint_record({
        "type": "report_generated",
        "identity": identity,
        "report_id": report_id,
        "fingerprint": report["fingerprint"],
        "timestamp": datetime.utcnow().isoformat()
    })

    # --- Cryptographic audit ---
    _append_osint_record(
        audit("report_generated", report)
    )

    return report



# shared.py (SEMANTIC SEARCH)

from backend.app.ingest import compute_text_embedding


from core.schema import require_keys
from core.audit import audit

def semantic_search(query: str, top_k: int = 5) -> dict:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if text_faiss is None:
        raise RuntimeError("Text FAISS not initialized")

    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")

    # --- Compute embedding ---
    embedding = compute_text_embedding(query)

    if not embedding or len(embedding) != text_faiss.dim:
        raise RuntimeError("Invalid query embedding")

    # --- FAISS search (read-only) ---
    results = text_faiss.search_by_vector(
        embedding,
        k=top_k
    )

    formatted = []
    for uid, score, meta in results:
        try:
            score_f = round(float(score), 6)
        except Exception:
            score_f = 0.0

        formatted.append({
            "uid": uid,
            "score": score_f,
            "source": meta.get("source"),
            "length": meta.get("length"),
            "type": meta.get("type", "text")
        })

    # Deterministic ordering (S8)
    formatted.sort(
        key=lambda x: (-x["score"], x["uid"])
    )

    result = {
        "query": query,
        "top_k": top_k,
        "results": formatted
    }

    # --- Schema guard (S8) ---
    require_keys(
        result,
        ["query", "top_k", "results"],
        ctx="semantic_search_output"
    )

    # --- Audit (read-only query) ---
    _append_osint_record(
        audit(
            "semantic_search",
            {
                "query": query,
                "top_k": top_k,
                "results": len(formatted)
            }
        )
    )

    return result



# shared.py (GLOBAL SEARCH)



def _normalize(q: str) -> str:
    return q.lower().strip()


def _contains(haystack, needle):
    try:
        return needle in haystack
    except Exception:
        return False


from core.schema import require_keys
from core.audit import audit

def global_search(query: str) -> dict:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    q = query.lower().strip()
    records = _load_osint_db()

    matches = {
        "identities": set(),
        "sources": set(),
        "images": [],
        "videos": [],
        "text": [],
        "git": [],
        "audio": [],
        "reports": [],
        "other": [],
    }

    for r in records:
        # Safe stringify (S8)
        try:
            raw = json.dumps(r, default=str).lower()
        except Exception:
            raw = ""

        r_type = r.get("type")
        src = r.get("source")

        # Identity hits
        if isinstance(r.get("identity"), str) and q in r["identity"].lower():
            matches["identities"].add(r["identity"])

        # Source hits
        if isinstance(src, str) and q in src.lower():
            matches["sources"].add(src)

        # Generic content hit
        if q not in raw:
            continue

        entry = {
            "type": r_type,
            "source": src,
            "record": r
        }

        if r_type in ("image", "image_advanced"):
            matches["images"].append(entry)
        elif r_type in ("video", "video_advanced"):
            matches["videos"].append(entry)
        elif r_type == "text":
            matches["text"].append(entry)
        elif r_type == "git":
            matches["git"].append(entry)
        elif r_type == "audio":
            matches["audio"].append(entry)
        elif r_type == "report_generated":
            matches["reports"].append(entry)
        else:
            matches["other"].append(entry)

    # Deterministic output (S8)
    result = {
        "query": query,
        "matches": {
            "identities": sorted(matches["identities"]),
            "sources": sorted(matches["sources"]),
            "images": matches["images"],
            "videos": matches["videos"],
            "text": matches["text"],
            "git": matches["git"],
            "audio": matches["audio"],
            "reports": matches["reports"],
            "other": matches["other"],
        }
    }

    # --- Schema guard (S8) ---
    require_keys(
        result,
        ["query", "matches"],
        ctx="global_search"
    )

    # --- Cryptographic audit (read-only) ---
    _append_osint_record(
        audit(
            "global_search",
            {
                "query": query,
                "hits": sum(
                    len(v)
                    for v in result["matches"].values()
                    if isinstance(v, list)
                )
            }
        )
    )

    return result

      
# shared.py (ADMIN PANEL)

from core.schema import require_keys
from core.audit import audit

def admin_system_status() -> dict:
    records = _load_osint_db()

    stats = {
        "total_records": len(records),
        "by_type": {},
        "faiss": {
            "image_vectors": faiss_manager.count() if faiss_manager else 0,
            "face_vectors": face_faiss.count() if face_faiss else 0,
            "text_vectors": text_faiss.count() if text_faiss else 0,
        },
        "last_updated": datetime.utcnow().isoformat(),
    }

    for r in records:
        t = r.get("type", "unknown")
        stats["by_type"][t] = stats["by_type"].get(t, 0) + 1

    require_keys(
        stats,
        ["total_records", "by_type", "faiss", "last_updated"],
        ctx="admin_system_status"
    )

    _append_osint_record(
        audit("admin_system_status", stats)
    )

    return stats


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        200_000
    ).hex()

def set_admin_password(password: str):
    if len(password) < 12:
        raise ValueError("Admin password must be at least 12 characters")

    salt = secrets.token_hex(16)
    pwd_hash = _hash_password(password, salt)

    data = {
        "salt": salt,
        "password_hash": pwd_hash,
        "created_at": datetime.utcnow().isoformat()
    }

    with open(ADMIN_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

    return {"status": "OK", "message": "Admin password set"}

def verify_admin_password(password: str) -> bool:
    if not os.path.exists(ADMIN_CONFIG_PATH):
        raise RuntimeError("Admin password not initialized")

    with open(ADMIN_CONFIG_PATH, "r") as f:
        data = json.load(f)

    test_hash = _hash_password(password, data["salt"])

    return hmac.compare_digest(test_hash, data["password_hash"])



from core.audit import audit

def admin_reload_indices() -> dict:
    _load_faiss_index()
    _load_face_faiss()
    _load_text_faiss_index()

    result = {
        "status": "OK",
        "message": "FAISS indices reloaded from disk",
        "timestamp": datetime.utcnow().isoformat()
    }

    _append_osint_record(
        audit("admin_reload_indices", result)
    )

    return result


def rebuild_all_indices():
    print("[AI] Rebuilding intelligence from stored data...")

    from backend.ai.intelligence_builder import rebuild_from_osint
    from backend.ai.semantic_engine import load_semantic

    rebuild_from_osint(OSINT_DB_PATH)
    load_semantic()

    print("[AI] Intelligence rebuilt successfully.")

from core.audit import audit

def admin_rebuild_indices(confirm: bool) -> dict:
    if not confirm:
        raise PermissionError("Rebuild not confirmed")

    rebuild_all_indices()

    result = {
        "status": "OK",
        "message": "FAISS indices rebuilt successfully",
        "timestamp": datetime.utcnow().isoformat()
    }

    _append_osint_record(
        audit("admin_rebuild_indices", result)
    )

    return result
def supervisor_wipe_all(phrase: str):
    """
    DANGEROUS: Irreversibly wipes ALL NEXINT data.
    Called only after multi-step confirmation in UI.
    """

    if phrase != "DELETE ALL NEXINT DATA":
        raise PermissionError("Invalid supervisor confirmation phrase")

    paths = [
        OSINT_DB_PATH,
        INDEX_PATH,
        META_PATH,
        TEXT_INDEX_PATH,
        TEXT_META_PATH,
        FACE_INDEX_PATH,
        FACE_META_PATH,
        FACE_IDENTITY_PATH,
        DATA_META_DIR,
    ]

    wiped = []

    for p in paths:
        try:
            if os.path.isfile(p):
                os.remove(p)
                wiped.append(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)
                wiped.append(p)
        except Exception as e:
            print(f"[WARN] Failed to remove {p}: {e}")

    # Reset FAISS runtime state
    try:
        if faiss_manager:
            faiss_manager.reset()
        if face_faiss:
            face_faiss.reset()
        if text_faiss:
            text_faiss.reset()
    except Exception as e:
        print(f"[WARN] Failed to reset FAISS state: {e}")

    _append_osint_record(
        audit(
            "supervisor_wipe_all",
            {
                "wiped_items": wiped,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    )

    return {
        "status": "OK",
        "message": "All NEXINT data wiped successfully",
        "deleted": wiped
    }


from core.audit import audit
from core.integrity import check_alignment

def admin_integrity_check() -> dict:
    issues = []

    try:
        if faiss_manager:
            check_alignment(faiss_manager, "image/video")
    except Exception as e:
        issues.append(str(e))

    try:
        check_alignment(face_faiss, "face")
    except Exception as e:
        issues.append(str(e))

    try:
        if text_faiss:
            check_alignment(text_faiss, "text")
    except Exception as e:
        issues.append(str(e))

    result = {
        "status": "OK" if not issues else "ISSUES_FOUND",
        "issues": issues,
        "checked_at": datetime.utcnow().isoformat()
    }

    _append_osint_record(
        audit("admin_integrity_check", result)
    )

    return result


from core.audit import audit

def admin_export_osint_snapshot(path: str) -> dict:
    if not path or not path.endswith(".json"):
        raise ValueError("Export path must be a .json file")

    records = _load_osint_db()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4)

    result = {
        "status": "OK",
        "exported_to": path,
        "records": len(records),
        "timestamp": datetime.utcnow().isoformat()
    }

    _append_osint_record(
        audit("admin_export_osint_snapshot", result)
    )

    return result






