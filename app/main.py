import json
import logging
import time
import urllib.parse
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import joblib
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Chemins vers les artefacts
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
VECTORIZER_PATH = MODELS_DIR / "vectorizer.pkl"
MODEL_PATH = MODELS_DIR / "model.pkl"
LOG_FILE_PATH = BASE_DIR / "cyberguard.log"

# --- 1. CONFIGURATION DU LOGGING ---
logger = logging.getLogger("cyberguard_security")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Écriture dans le fichier cyberguard.log avec encodage UTF-8
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Variables globales
vectorizer = None
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (chargement et nettoyage des artefacts)."""
    global vectorizer, model

    if not VECTORIZER_PATH.exists() or not MODEL_PATH.exists():
        raise RuntimeError("Les artefacts du modèle sont introuvables dans models/. Exécutez train.py d'abord.")

    vectorizer = joblib.load(VECTORIZER_PATH)
    model = joblib.load(MODEL_PATH)
    print("Artefacts de modèle chargés avec succès.")

    yield

    vectorizer = None
    model = None


app = FastAPI(
    title="CyberGuard WAF Engine API",
    description="API de détection en temps réel d'attaques SQLi, XSS et Prompt Injection.",
    version="1.0.0",
    lifespan=lifespan
)


def clean_payload(text: str) -> str:
    """Normalise la requête reçue."""
    if not isinstance(text, str):
        return ""
    decoded = urllib.parse.unquote(text)
    cleaned = " ".join(decoded.split())
    return cleaned.lower()


class InspectionRequest(BaseModel):
    payload: str


class InspectionResponse(BaseModel):
    payload: str
    is_malicious: bool
    action: str
    confidence: float


@app.get("/")
def health_check() -> Dict[str, str]:
    """Endpoint de santé pour vérifier l'état du service."""
    return {"status": "online", "service": "CyberGuard WAF Engine"}


@app.post("/api/v1/inspect", response_model=InspectionResponse)
async def inspect_payload(request_data: InspectionRequest, req: Request) -> Dict[str, Any]:
    """
    Analyse un payload web et détermine s'il est malveillant ou légitime.
    """
    start_time = time.time()

    if vectorizer is None or model is None:
        raise HTTPException(
            status_code=500,
            detail="Le modèle ML n'a pas été initialisé correctement."
        )

    if not request_data.payload.strip():
        raise HTTPException(status_code=400, detail="Le payload ne peut pas être vide.")

    # Nettoyage et vectorisation
    cleaned = clean_payload(request_data.payload)
    vec = vectorizer.transform([cleaned])

    # Prédiction et probabilités
    prediction = int(model.predict(vec)[0])
    probabilities = model.predict_proba(vec)[0]
    confidence = float(probabilities[prediction])

    is_malicious = (prediction == 1)
    action = "BLOCK" if is_malicious else "ALLOW"
    execution_time_ms = round((time.time() - start_time) * 1000, 2)

    # --- 2. LOGGING DANS CYBERGUARD.LOG ---
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_ip": req.client.host if req.client else "unknown",
        "method": req.method,
        "path": req.url.path,
        "payload": request_data.payload,
        "is_malicious": is_malicious,
        "action": action,
        "confidence": round(confidence, 4),
        "execution_time_ms": execution_time_ms
    }

    if is_malicious:
        logger.warning(json.dumps(log_entry, ensure_ascii=False))
    else:
        logger.info(json.dumps(log_entry, ensure_ascii=False))

    return {
        "payload": request_data.payload,
        "is_malicious": is_malicious,
        "action": action,
        "confidence": round(confidence, 4)
    }