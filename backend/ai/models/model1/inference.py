# inference.py
import os
from features import FeatureBuilder
from model import DecisionModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "decision_model_v1.pkl")

feature_builder = FeatureBuilder()
decision_model = DecisionModel(MODEL_PATH)


def run_decision_engine(evidence: dict):
    features = feature_builder.build(evidence)
    result = decision_model.predict(features)
    return result

evidence = {
    "face_similarity": 0.91,
    "image_quality": 0.82,
    "metadata_similarity": 0.70,
    "username_similarity": 0.65,
    "source_count": 3,
    "platform_overlap": 2,
    "temporal_distance_days": 5
}

output = run_decision_engine(evidence)
print(output)

stress_tests = [
    {
        "face_similarity": 0.92,
        "image_quality": 0.85,
        "metadata_similarity": 0.20,
        "username_similarity": 0.30,
        "source_count": 1,
        "platform_overlap": 0,
        "temporal_distance_days": 90
    },
    {
        "face_similarity": 0.78,
        "image_quality": 0.70,
        "metadata_similarity": 0.88,
        "username_similarity": 0.82,
        "source_count": 5,
        "platform_overlap": 4,
        "temporal_distance_days": 2
    },
    {
        "face_similarity": 0.83,
        "image_quality": 0.75,
        "metadata_similarity": 0.50,
        "username_similarity": 0.55,
        "source_count": 2,
        "platform_overlap": 1,
        "temporal_distance_days": 35
    }
]

for case in stress_tests:
    print(run_decision_engine(case))
