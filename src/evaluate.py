import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score

# Definition des chemins
BASE_DIR = Path(__file__).resolve().parent.parent
TEST_DATA_PATH = BASE_DIR / "data" / "processed" / "test.csv"
MODELS_DIR = BASE_DIR / "models"
METRICS_PATH = BASE_DIR / "metrics.json"


def evaluate_model():
    """
    Evalue le modele sur le jeu de test et enregistre les metriques dans metrics.json.
    """
    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(f"Fichier de test introuvable : {TEST_DATA_PATH}")

    vectorizer_path = MODELS_DIR / "vectorizer.pkl"
    model_path = MODELS_DIR / "model.pkl"

    if not vectorizer_path.exists() or not model_path.exists():
        raise FileNotFoundError("Artefacts du modele introuvables. Executez train.py d'abord.")

    print("Chargement des donnees de test et du modele...")
    df_test = pd.read_csv(TEST_DATA_PATH)
    X_test_text = df_test["cleaned_payload"].fillna("").astype(str)
    y_test = df_test["label"]

    vectorizer = joblib.load(vectorizer_path)
    model = joblib.load(model_path)

    print("Prediction sur le jeu de test...")
    X_test_vec = vectorizer.transform(X_test_text)
    y_pred = model.predict(X_test_vec)

    # Calcul des metriques
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    metrics = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4)
    }

    print("\n--- Rapport d'Evaluation ---")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Sauvegarde des metriques en JSON
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)

    print(f"Metriques sauvegardees dans : {METRICS_PATH}")


def main():
    try:
        evaluate_model()
    except Exception as e:
        print(f"Erreur lors de l'evaluation : {e}")


if __name__ == "__main__":
    main()