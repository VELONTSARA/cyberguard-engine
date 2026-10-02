from pathlib import Path
import re
import urllib.parse
import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import PROCESSED_DIR, RAW_DATA_PATH


def clean_payload(text: str) -> str:
    """
    Normalise un payload brut :
    - Décodage URL
    - Conversion en minuscules
    - Tokenisation des adresses IP, UUIDs et nombres
    """
    if not isinstance(text, str):
        return ""

    # 1. Décodage URL (%20 -> espace, %27 -> ', etc.)
    decoded = urllib.parse.unquote(text)

    # 2. Passage en minuscules
    cleaned = decoded.lower()

    # 3. Remplacement des adresses IP par <IP>
    cleaned = re.sub(
        r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "<IP>", cleaned
    )

    # 4. Remplacement des UUIDs par <UUID>
    cleaned = re.sub(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        "<UUID>",
        cleaned,
    )

    # 5. Remplacement des nombres isolés par <NUM>
    cleaned = re.sub(r"\b\d+\b", "<NUM>", cleaned)

    # 6. Normalisation des espaces multiples
    cleaned = " ".join(cleaned.split())

    return cleaned


def process_and_split_data():
    """
    Charge les données brutes, applique le nettoyage et découpe en train/test.
    """
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {RAW_DATA_PATH}")

    print("Chargement des données brutes...")
    df = pd.read_csv(RAW_DATA_PATH)

    print("Application du nettoyage et de la tokenisation...")
    df["cleaned_payload"] = df["payload"].apply(clean_payload)

    print("Séparation Train/Test stratifiée...")
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["category"],
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    train_path = PROCESSED_DIR / "train.csv"
    test_path = PROCESSED_DIR / "test.csv"

    train_df.to_csv(train_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")

    print(f"Échantillons entraînement : {len(train_df)} -> {train_path}")
    print(f"Échantillons test         : {len(test_df)} -> {test_path}")


def main():
    try:
        process_and_split_data()
        print("Prétraitement terminé avec succès !")
    except Exception as e:
        print(f"Erreur lors du prétraitement : {e}")


if __name__ == "__main__":
    main()