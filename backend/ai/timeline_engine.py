import json
import os
from datetime import datetime

def build_timeline(osint_db_path, metadata_dir):
    timeline = []

    # OSINT records
    if os.path.exists(osint_db_path):
        with open(osint_db_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for r in records:
            ts = r.get("timestamp")
            if ts:
                timeline.append({
                    "time": ts,
                    "type": r.get("type"),
                    "source": r.get("source"),
                    "details": r
                })

    # Media metadata
    for root, _, files in os.walk(metadata_dir):
        for f in files:
            if not f.endswith(".json"):
                continue
            path = os.path.join(root, f)

            try:
                with open(path, "r") as fh:
                    data = json.load(fh)
            except Exception:
                continue

            fmt = data.get("metadata", {}).get("format", {})
            tags = fmt.get("tags", {})
            ct = tags.get("creation_time")

            if ct:
                timeline.append({
                    "time": ct,
                    "type": "media",
                    "source": data.get("source"),
                    "details": data
                })

    # Sort safely
    timeline.sort(key=lambda x: x["time"])
    return timeline



DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
META_DIR = os.path.join(DATA_DIR, "media_metadata")

def _parse_time(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", ""))
    except Exception:
        return None

def build_investigation_timeline(case_filter=None):
    """
    Extended investigation timeline:
    - OSINT records
    - Media metadata (image/video)
    - Face appearances
    """

    events = []
    case_filter_norm = case_filter.lower() if case_filter else None

    # -----------------------------
    # 1️⃣ OSINT RECORDS
    # -----------------------------
    osint_path = os.path.join(DATA_DIR, "osint_records.json")
    if os.path.exists(osint_path):
        try:
            with open(osint_path, "r") as f:
                records = json.load(f)
        except Exception:
            records = []

        for r in records:
            if not isinstance(r, dict):
                continue

            src = r.get("source")
            identity = r.get("identity")

            # 🔎 case filter (identity OR source)
            if case_filter_norm:
                blob = f"{identity} {src} {r}".lower()
                if case_filter_norm not in blob:
                    continue

            ts = (
                r.get("timestamp")
                or r.get("created_at")
                or datetime.utcnow().isoformat()
            )

            events.append({
                "timestamp": ts,
                "source": src,
                "identity": identity,
                "event_type": r.get("type", "osint"),
                "description": r.get(
                    "description",
                    f"OSINT scan on {src}"
                )
            })

    # -----------------------------
    # 2️⃣ MEDIA METADATA (EXIF / ffprobe)
    # -----------------------------
    for root, _, files in os.walk(META_DIR):
        for fname in files:
            if not fname.endswith(".json"):
                continue

            try:
                with open(os.path.join(root, fname)) as jf:
                    meta = json.load(jf)
            except Exception:
                continue

            if not isinstance(meta, dict):
                continue

            src = meta.get("source")
            if not src:
                continue

            # 🔎 case filter
            if case_filter_norm and case_filter_norm not in str(meta).lower():
                continue

            fmt = meta.get("metadata", {}).get("format", {})
            ts = (
                fmt.get("tags", {}).get("creation_time")
                or meta.get("timestamp")
                or datetime.utcnow().isoformat()
            )

            events.append({
                "timestamp": ts,
                "source": src,
                "identity": None,
                "event_type": "media_metadata",
                "description": "Metadata extracted (EXIF / ffprobe)"
            })

    # -----------------------------
    # 3️⃣ FACE APPEARANCES (IDENTITY TIMELINE)
    # -----------------------------
    face_meta_path = os.path.join(DATA_DIR, "face_faiss_meta.json")
    if os.path.exists(face_meta_path):
        try:
            with open(face_meta_path, "r") as f:
                face_meta = json.load(f)
        except Exception:
            face_meta = {}

        if isinstance(face_meta, dict):
            for uid, entry in face_meta.items():
                if not isinstance(entry, dict):
                    continue

                identity = entry.get("identity")
                src = entry.get("source")

                if not src:
                    continue

                # 🔎 case filter (identity OR source)
                if case_filter_norm:
                    blob = f"{identity} {src}".lower()
                    if case_filter_norm not in blob:
                        continue

                ts = entry.get("timestamp") or datetime.utcnow().isoformat()

                events.append({
                    "timestamp": ts,
                    "source": src,
                    "identity": identity,
                    "event_type": "face_appearance",
                    "description": f"Face detected: {identity or 'UNKNOWN'}"
                })

    # -----------------------------
    # SORT CHRONOLOGICALLY (SAFE)
    # -----------------------------
    events.sort(
        key=lambda e: _parse_time(e.get("timestamp")) or datetime.max
    )

    return events


def build_exposure_graph(timeline_events):
    """
    Convert timeline events into graph nodes & edges
    """
    nodes = {}
    edges = []

    for evt in timeline_events:
        src = evt.get("source")
        identity = evt.get("identity")
        etype = evt.get("event_type")

        if identity:
            nodes.setdefault(identity, {"type": "identity"})
            nodes.setdefault(src, {"type": "source"})
            edges.append((identity, src, etype))

    return nodes, edges



def reconstruct_timeline(events):
    """
    Sort semantic search results by timestamp if available
    """
    def safe_time(e):
        return e.get("timestamp") or ""

    return sorted(events, key=safe_time)
