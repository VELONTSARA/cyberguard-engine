from pathlib import Path
import urllib.parse
import pandas as pd
from sklearn.model_selection import train_test_split

# Definition des chemins
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "payloads.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def clean_payload(text: str) -> str:
    """
    Normalise un payload brut (decodage URL, passage en minuscules et nettoyage).
    """
    if not isinstance(text, str):
        return ""

    # Decodage URL simple (%20 -> espace, %27 -> ', etc.)
    decoded = urllib.parse.unquote(text)

    # Nettoyage des espaces multiples et passage en minuscules
    cleaned = " ".join(decoded.split())

    return cleaned.lower()


def process_and_split_data():
    """
    Charge les donnees brutes, applique le nettoyage et decoupe en train/test.
    """
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {RAW_DATA_PATH}")

    # Chargement du dataset brut
    print("Chargement des donnees brutes...")
    df = pd.read_csv(RAW_DATA_PATH)

    # Application de la normalisation
    df["cleaned_payload"] = df["payload"].apply(clean_payload)

    # Separation en jeu d'entrainement (80%) et de test (20%)
    print("Separation Train/Test stratifiee...")
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["category"]
    )

    # Verification du dossier de sortie
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Sauvegarde des fichiers
    train_path = PROCESSED_DIR / "train.csv"
    test_path = PROCESSED_DIR / "test.csv"

    train_df.to_csv(train_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")

    print(f"Echantillons entrainement : {len(train_df)} -> {train_path}")
    print(f"Echantillons test         : {len(test_df)} -> {test_path}")


def main():
    try:
        process_and_split_data()
        print("Pretraitement termine avec succes !")
    except Exception as e:
        print(f"Erreur lors du pretraitement : {e}")


if __name__ == "__main__":
    main()