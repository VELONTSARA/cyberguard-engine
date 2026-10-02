from pathlib import Path

# 1. Racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Dossiers et chemins des données
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_DATA_PATH = DATA_RAW_DIR / "payloads.csv"
TRAIN_DATA_PATH = PROCESSED_DIR / "train.csv"
TEST_DATA_PATH = PROCESSED_DIR / "test.csv"

# 3. Dossiers et chemins des artefacts (Modèles et Vectoriseur)
MODELS_DIR = BASE_DIR / "models"
VECTORIZER_PATH = MODELS_DIR / "vectorizer.pkl"
MODEL_PATH = MODELS_DIR / "model.pkl"

# 4. Fichier des métriques d'évaluation
METRICS_PATH = BASE_DIR / "metrics.json"

# 5. Configuration globale du WAF
WAF_THRESHOLD = 0.65