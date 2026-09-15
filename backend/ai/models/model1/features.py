# features.py

from typing import Dict, List
from config import FEATURE_ORDER


class FeatureBuilder:
    """
    Converts raw OSINT evidence into ML-ready feature vectors.
    """

    def __init__(self):
        self.feature_order = FEATURE_ORDER

    def build(self, evidence: Dict) -> List[float]:
        """
        evidence: dict containing extracted OSINT signals
        returns: ordered numeric feature vector
        """

        features = {
            "face_similarity": float(evidence.get("face_similarity", 0.0)),
            "image_quality": float(evidence.get("image_quality", 0.0)),
            "metadata_similarity": float(evidence.get("metadata_similarity", 0.0)),
            "username_similarity": float(evidence.get("username_similarity", 0.0)),
            "source_count": int(evidence.get("source_count", 0)),
            "platform_overlap": int(evidence.get("platform_overlap", 0)),
            "temporal_distance_days": int(evidence.get("temporal_distance_days", 999))
        }

        return [features[name] for name in self.feature_order]
