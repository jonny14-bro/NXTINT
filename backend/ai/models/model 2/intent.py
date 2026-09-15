# intent.py

INTENT_PATTERNS = {
    "WHY_DECISION": [
        "why", "reason", "rationale", "explain", "basis", "logic"
    ],
    "CONFIDENCE_MEANING": [
        "confidence", "reliable", "certainty", "trust", "probability"
    ],
    "WHAT_EVIDENCE_MISSING": [
        "missing", "need more", "insufficient", "lack", "required"
    ],
    "CAN_WE_CONFIRM": [
        "confirm", "finalize", "sure", "verified"
    ],
    "COMPARE_CASES": [
        "compare", "difference", "versus", "vs"
    ],
    "NEXT_STEPS": [
        "next", "do now", "proceed", "steps", "action"
    ],
    "TIMELINE_VIEW": [
        "timeline", "first seen", "last seen", "when seen", "history", "appearance history"
    ]
}

DEFAULT_INTENT = "RISK_ASSESSMENT"


def detect_intents(query: str):
    q = query.lower()
    detected = []

    for intent, keywords in INTENT_PATTERNS.items():
        for kw in keywords:
            if kw in q:
                detected.append(intent)
                break  # avoid duplicate intent

    if not detected:
        detected.append(DEFAULT_INTENT)

    return detected

