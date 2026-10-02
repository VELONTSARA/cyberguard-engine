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
from fastapi.responses import HTMLResponse
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


@app.get("/", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Endpoint de santé pour vérifier l'état du service."""
    return {"status": "online", "service": "CyberGuard WAF Engine"}


@app.post("/api/v1/inspect", response_model=InspectionResponse, tags=["WAF Inspection"])
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

    # --- LOGGING DANS CYBERGUARD.LOG ---
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


# --- 2. DASHBOARD HTML & CHART.JS ---
@app.get("/dashboard", response_class=HTMLResponse, tags=["Monitoring"])
def get_dashboard():
    """Génère un tableau de bord analytique basé sur le fichier cyberguard.log."""
    logs = []
    if LOG_FILE_PATH.exists():
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    total_requests = len(logs)
    blocked_requests = sum(1 for log in logs if log.get("action") == "BLOCK")
    allowed_requests = total_requests - blocked_requests

    avg_latency = (
        round(sum(log.get("execution_time_ms", 0) for log in logs) / total_requests, 2)
        if total_requests > 0 else 0.0
    )

    recent_logs = list(reversed(logs[-10:]))

    recent_rows_html = ""
    for log in recent_logs:
        badge_class = "badge-block" if log.get("action") == "BLOCK" else "badge-allow"
        recent_rows_html += f"""
        <tr>
            <td>{log.get('timestamp', '')[:19]}</td>
            <td><code>{log.get('client_ip', 'unknown')}</code></td>
            <td><code>{log.get('payload', '')[:40]}</code></td>
            <td><span class="{badge_class}">{log.get('action')}</span></td>
            <td>{log.get('confidence', 0):.2f}</td>
            <td>{log.get('execution_time_ms', 0)} ms</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>CyberGuard WAF - Monitoring</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; background-color: #0f172a; color: #f8fafc; }}
            h1 {{ margin-bottom: 20px; font-size: 24px; color: #38bdf8; }}
            .stats {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; border: 1px solid #334155; }}
            .card h3 {{ margin: 0; color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
            .card p {{ font-size: 28px; font-weight: bold; margin: 10px 0 0 0; }}
            .grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; margin-bottom: 30px; }}
            .panel {{ background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
            th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #334155; }}
            th {{ color: #94a3b8; font-weight: 600; }}
            .badge-block {{ background: #ef4444; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .badge-allow {{ background: #22c55e; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>🛡️ CyberGuard Engine - Dashboard Observabilité</h1>

        <div class="stats">
            <div class="card"><h3>Total Requêtes</h3><p>{total_requests}</p></div>
            <div class="card"><h3>Attaques Bloquées</h3><p style="color: #ef4444;">{blocked_requests}</p></div>
            <div class="card"><h3>Trafic Légitime</h3><p style="color: #22c55e;">{allowed_requests}</p></div>
            <div class="card"><h3>Latence Moyenne</h3><p style="color: #38bdf8;">{avg_latency} ms</p></div>
        </div>

        <div class="grid">
            <div class="panel">
                <h3>Répartition du Trafic</h3>
                <canvas id="trafficChart" style="max-height: 250px;"></canvas>
            </div>
            <div class="panel">
                <h3>Dernières Requêtes Analysées</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Horodatage</th>
                            <th>IP</th>
                            <th>Payload</th>
                            <th>Action</th>
                            <th>Confiance</th>
                            <th>Latence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recent_rows_html if recent_rows_html else '<tr><td colspan="6">Aucun log enregistré.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('trafficChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['ALLOW', 'BLOCK'],
                    datasets: [{{
                        data: [{allowed_requests}, {blocked_requests}],
                        backgroundColor: ['#22c55e', '#ef4444'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }} }},
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)