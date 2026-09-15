# explain.py

from config import FEATURE_ORDER


def explain_prediction(feature_vector):
    """
    Rule-based explanation (safe & court-friendly).
    """

    explanations = []

    fv = dict(zip(FEATURE_ORDER, feature_vector))

    if fv["face_similarity"] > 0.85:
        explanations.append("High face similarity detected")

    if fv["source_count"] < 2:
        explanations.append("Low number of corroborating sources")

    if fv["metadata_similarity"] < 0.4:
        explanations.append("Metadata inconsistency observed")

    if fv["temporal_distance_days"] > 30:
        explanations.append("Large temporal gap between evidences")

    if not explanations:
        explanations.append("No strong indicators detected")

    return explanations
