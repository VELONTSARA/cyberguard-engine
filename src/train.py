import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.naive_bayes import MultinomialNB
from src.config import (
    MODEL_PATH,
    MODELS_DIR,
    TEST_DATA_PATH,
    TRAIN_DATA_PATH,
    VECTORIZER_PATH,
)


def train_and_select_best_model():
    if not TRAIN_DATA_PATH.exists() or not TEST_DATA_PATH.exists():
        raise FileNotFoundError("Fichiers train.csv ou test.csv introuvables.")

    print("1. Chargement des données...")
    df_train = pd.read_csv(TRAIN_DATA_PATH)
    df_test = pd.read_csv(TEST_DATA_PATH)

    X_train_text = df_train["cleaned_payload"].fillna("").astype(str)
    y_train = df_train["label"]
    X_test_text = df_test["cleaned_payload"].fillna("").astype(str)
    y_test = df_test["label"]

    print("2. Extraction TF-IDF (char_wb n-grams 2 à 5, sublinear_tf=True)...")
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        sublinear_tf=True,
        min_df=1,
    )
    X_train_vec = vectorizer.fit_transform(X_train_text)
    X_test_vec = vectorizer.transform(X_test_text)

    candidate_models = {
        "Logistic Regression": LogisticRegression(C=2.0, max_iter=500, random_state=42),
        "Naive Bayes": MultinomialNB(alpha=0.5),
        "Random Forest": RandomForestClassifier(
            n_estimators=150, max_depth=15, random_state=42
        ),
    }

    best_model = None
    best_f1 = -1.0
    best_name = ""

    print("\n3. Benchmark des modèles...\n")
    print(
        f"{'Modèle':<22} | {'Accuracy':<10} | {'Précision':<10} | {'Rappel':<10} | {'F1-Score':<10}"
    )
    print("-" * 75)

    for name, model in candidate_models.items():
        model.fit(X_train_vec, y_train)
        y_pred = model.predict(X_test_vec)

        acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average="binary", zero_division=0
        )

        print(
            f"{name:<22} | {acc:<10.4f} | {prec:<10.4f} | {rec:<10.4f} | {f1:<10.4f}"
        )

        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_name = name

    print("-" * 75)
    print(
        f"\n--> MEILLEUR MODÈLE RETENU : [{best_name}] (F1-Score: {best_f1:.4f})"
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(best_model, MODEL_PATH)

    print(f"[OK] Vectoriseur sauvegardé dans : {VECTORIZER_PATH}")
    print(f"[OK] Modèle sauvegardé dans       : {MODEL_PATH}")


if __name__ == "__main__":
    train_and_select_best_model()