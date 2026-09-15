# core/integrity.py
def check_alignment(mgr, name):
    if mgr.count() != mgr.meta_count():
        raise RuntimeError(f"[INTEGRITY] {name} FAISS mismatch")
