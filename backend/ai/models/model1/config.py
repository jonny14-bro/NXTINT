# config.py

LABELS = {
    0: "NO MATCH",
    1: "POSSIBLE MATCH",
    2: "CONFIRMED MATCH"
}

CONFIDENCE_THRESHOLDS = {
    "HIGH": 0.85,
    "MEDIUM": 0.60
}

FEATURE_ORDER = [
    "face_similarity",
    "image_quality",
    "metadata_similarity",
    "username_similarity",
    "source_count",
    "platform_overlap",
    "temporal_distance_days"
]
