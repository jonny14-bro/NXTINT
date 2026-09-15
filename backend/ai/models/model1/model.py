# model.py

import joblib
import numpy as np
from config import LABELS
from explain import explain_prediction
import json, time
from config import FEATURE_ORDER

def audit_log(evidence, result):
    record = {
        "timestamp": time.time(),
        "evidence": evidence,
        "decision": result
    }
    with open("audit.log", "a") as f:
        f.write(json.dumps(record) + "\n")

def confidence_band(conf):
    if conf >= 0.85:
        return "HIGH"
    elif conf >= 0.60:
        return "MEDIUM"
    else:
        return "LOW"

class DecisionModel:
    """
    Wrapper around trained ML model.
    """

    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

    def predict(self, feature_vector):
        X = np.array(feature_vector).reshape(1, -1)

        probs = self.model.predict_proba(X)[0]
        predicted_class = int(np.argmax(probs))
        confidence = float(probs[predicted_class])

        fv = dict(zip(FEATURE_ORDER, feature_vector))

        # 🔒 False-positive suppression
        if predicted_class == 2:
            if fv["source_count"] < 3:
                predicted_class = 1
                confidence *= 0.7

            if fv["metadata_similarity"] < 0.5:
                predicted_class = 1
                confidence *= 0.6

            if fv["temporal_distance_days"] > 30:
                predicted_class = 1
                confidence *= 0.6

        explanation = explain_prediction(feature_vector)

        result = {
            "decision": LABELS[predicted_class],
            "confidence": round(confidence, 4),
            "confidence_level": confidence_band(confidence),
            "explanation": explanation
        }

        audit_log(feature_vector, result)
        return result

