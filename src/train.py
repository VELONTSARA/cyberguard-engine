from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Definition des chemins
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DATA_PATH = BASE_DIR / "data" / "processed" / "train.csv"
MODELS_DIR = BASE_DIR / "models"


def train_model():
    """
    Entraine le vectoriseur TF-IDF et le modele de classification,
    puis sauvegarde les artefacts dans le dossier models/.
    """
    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(f"Fichier d'entrainement introuvable : {TRAIN_DATA_PATH}")

    print("Chargement des donnees d'entrainement...")
    df_train = pd.read_csv(TRAIN_DATA_PATH)

    # Nettoyage securite : conversion explicite en chaines de caracteres
    X_train_text = df_train["cleaned_payload"].fillna("").astype(str)
    y_train = df_train["label"]

    print("Extraction des caracteristiques (TF-IDF char n-grams)...")
    # Utilisation de n-grams de caracteres (2 a 5) pour capter la syntaxe des attaques
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5))
    X_train_vec = vectorizer.fit_transform(X_train_text)

    print("Entrainement du modele (Logistic Regression)...")
    model = LogisticRegression(random_state=42)
    model.fit(X_train_vec, y_train)

    # Verification et creation du dossier de sortie
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    vectorizer_path = MODELS_DIR / "vectorizer.pkl"
    model_path = MODELS_DIR / "model.pkl"

    # Sauvegarde des objets
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(model, model_path)

    print(f"Vectoriseur sauvegarde dans : {vectorizer_path}")
    print(f"Modele sauvegarde dans      : {model_path}")


def main():
    try:
        train_model()
        print("Entrainement termine avec succes !")
    except Exception as e:
        print(f"Erreur lors de l'entrainement : {e}")


if __name__ == "__main__":
    main()