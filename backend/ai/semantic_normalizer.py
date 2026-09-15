
import hashlib


def normalize_osint_record(rec: dict) -> str:
    parts = []

    rtype = rec.get("type")
    src = rec.get("source")

    parts.append(f"Record type: {rtype}")
    parts.append(f"Source: {src}")

    if rtype == "image":
        exif = rec.get("exif", {})
        if exif.get("gps"):
            parts.append(f"GPS location: {exif['gps']}")
        if exif.get("timestamp"):
            parts.append(f"Captured at {exif['timestamp']}")

    if rtype == "video":
        parts.append(f"Video frames analyzed: {rec.get('num_frames')}")

    if rtype == "face":
        parts.append(f"Faces detected: {rec.get('faces_detected')}")

    if rtype == "text_security_scan":
        osint = rec.get("osint", {})
        if osint.get("emails"):
            parts.append(f"Emails found: {', '.join(osint['emails'][:5])}")
        if osint.get("phones"):
            parts.append(f"Phone numbers found: {', '.join(osint['phones'][:5])}")

    if rtype == "git":
        parts.append(f"Repository scanned for secrets")
        parts.append(f"Findings count: {rec.get('findings_count', 0)}")

    return ". ".join(parts)

def normalize_media_metadata(meta: dict) -> str:
    parts = []

    src = meta.get("source")
    parts.append(f"Media file: {src}")

    fmt = meta.get("metadata", {}).get("format", {})
    tags = fmt.get("tags", {})

    if tags.get("creation_time"):
        parts.append(f"Created at {tags['creation_time']}")

    gps = meta.get("metadata", {}).get("gps")
    if gps:
        parts.append(f"GPS location {gps}")

    streams = meta.get("metadata", {}).get("streams", [])
    for s in streams:
        if s.get("codec_type") == "video":
            parts.append(
                f"Video stream resolution {s.get('width')}x{s.get('height')} codec {s.get('codec_name')}"
            )

    return ". ".join(parts)


def semantic_fingerprint(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()


import re

TIME_KEYWORDS = [
    "before", "after", "earlier", "later",
    "first", "last", "sequence", "timeline",
    "chronological", "previous"
]

def detect_timeline_intent(query: str) -> bool:
    q = query.lower()
    return any(word in q for word in TIME_KEYWORDS)
