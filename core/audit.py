# core/audit.py
import hashlib, json, time

def audit(action: str, payload: dict):
    return {
        "type": "audit",
        "ts": time.time(),
        "action": action,
        "hash": hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()
    }
