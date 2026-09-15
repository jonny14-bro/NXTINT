# core/schema.py
def require_keys(obj: dict, keys: list, ctx: str):
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ValueError(f"[SCHEMA:{ctx}] Missing keys: {missing}")

def clamp_confidence(v):
    try:
        v = float(v)
    except Exception:
        return 0.0
    return max(0.0, min(round(v, 2), 100.0))
