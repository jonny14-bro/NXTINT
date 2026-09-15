# train.py

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from config import FEATURE_ORDER
from sklearn.calibration import CalibratedClassifierCV


DATASET_PATH = "training_data.csv"
MODEL_OUTPUT_PATH = "decision_model_v1.pkl"


def load_dataset(path):
    df = pd.read_csv(path)
    X = df[FEATURE_ORDER]
    y = df["label"]
    return X, y


def create_model():
    base_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_split=3,
        min_samples_leaf=3,
        random_state=42,
        class_weight="balanced"
    )

    calibrated_model = CalibratedClassifierCV(
        base_model,
        method="isotonic",
        cv=5
    )

    return calibrated_model



def evaluate_model(model, X_test, y_test):
    predictions = model.predict(X_test)

    print("\n📊 Classification Report")
    print(classification_report(y_test, predictions))

    print("\n🧩 Confusion Matrix")
    print(confusion_matrix(y_test, predictions))


def main():
    print("[*] Loading dataset...")
    X, y = load_dataset(DATASET_PATH)

    print("[*] Initializing model...")
    model = create_model()

    print("[*] Running 5-fold cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"📈 CV Accuracy: {cv_scores.mean():.4f}")

    print("[*] Splitting train/test data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print("[*] Training decision model...")
    model.fit(X_train, y_train)

    print("[*] Evaluating model...")
    evaluate_model(model, X_test, y_test)

    print("[*] Saving model...")
    joblib.dump(model, MODEL_OUTPUT_PATH)
    print(f"[✓] Model saved as {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
