# timeline.py

from datetime import datetime

def build_timeline(sources):
    events = []

    for src in sources:
        if "timestamp" not in src:
            continue

        try:
            ts = datetime.fromisoformat(src["timestamp"])
        except Exception:
            continue

        events.append({
            "time": ts,
            "source": src.get("file") or src.get("platform"),
            "type": src.get("type"),
            "confidence": src.get("confidence", "unknown")
        })

    events.sort(key=lambda x: x["time"])
    return events
