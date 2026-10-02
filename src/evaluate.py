import json
import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from src.config import METRICS_PATH, MODEL_PATH, TEST_DATA_PATH, VECTORIZER_PATH


def evaluate_model():
    """
    Évalue le modèle retenu sur le jeu de test et enregistre les métriques dans metrics.json.
    """
    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Fichier de test introuvable : {TEST_DATA_PATH}"
        )

    if not VECTORIZER_PATH.exists() or not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Artefacts du modèle introuvables. Exécutez train.py d'abord."
        )

    print("Chargement des données de test et du modèle...")
    df_test = pd.read_csv(TEST_DATA_PATH)
    X_test_text = df_test["cleaned_payload"].fillna("").astype(str)
    y_test = df_test["label"]

    vectorizer = joblib.load(VECTORIZER_PATH)
    model = joblib.load(MODEL_PATH)

    print("Inférence en cours sur le jeu de test...")
    X_test_vec = vectorizer.transform(X_test_text)
    y_pred = model.predict(X_test_vec)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    metrics = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
    }

    print("\n" + "=" * 60)
    print("         RAPPORT D'ÉVALUATION DU MODÈLE RETENU")
    print("=" * 60)

    print("\n1. MATRICE DE CONFUSION :")
    print(f"   • Vrais Négatifs (Requêtes saines bloquées : Non) : {tn}")
    print(f"   • Faux Positifs (Fausses alertes / Faux positifs) : {fp}")
    print(f"   • Faux Négatifs (Attaques manquées - DANGER)     : {fn}")
    print(f"   • Vrais Positifs (Attaques bien bloquées)        : {tp}")

    print("\n2. DÉTAILS PAR CLASSE :")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["Légitime (0)", "Attaque (1)"],
            zero_division=0,
        )
    )

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)

    print("=" * 60)
    print(f"[OK] Métriques enregistrées dans : {METRICS_PATH}")


def main():
    try:
        evaluate_model()
    except Exception as e:
        print(f"Erreur lors de l'évaluation : {e}")


if __name__ == "__main__":
    main()