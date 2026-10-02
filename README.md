# 🛡️ CyberGuard Engine

> Moteur WAF (Web Application Firewall) basé sur l'IA et le Machine Learning pour la détection et le blocage en temps réel d'attaques Web (SQLi, XSS, Path Traversal, Command Injection).

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E.svg)
![Pytest](https://img.shields.io/badge/tested%20with-pytest-blue.svg)

---

## Présentation du Projet

**CyberGuard Engine** est un microservice MLOps d'analyse de sécurité alimenté par du Machine Learning. Il analyse le contenu des payloads HTTP reçus et prend une décision d'inspection immédiate (`ALLOW` ou `BLOCK`) grâce à une classification supervisée.

### Fonctionnalités Clés
- **Détection Multi-vectorielle** : Détection ciblée des injections SQL, XSS (Cross-Site Scripting), Traversées de répertoires (*Path Traversal*) et Injections de commandes.
- **Extraction par $n$-grammes** : Extraction de caractéristiques par $n$-grammes de caractères TF-IDF (`char_wb` $2\text{--}5$), résistant à l'obfuscation et à l'URL Encoding.
- **Inférence Ultra-Rapide** : Exposition REST via **FastAPI** avec des temps de réponse en quelques millisecondes.
- **Architecture MLOps & CI/CD** : Pipeline d'entraînement automatisé, tests d'intégration avec **Pytest** (6/6 tests validés), et validation continue via **GitHub Actions**.

---

## Tech Stack

- **Langage** : Python 3.11
- **ML & Data** : Scikit-Learn (Régression Logistique, Random Forest), Pandas, Joblib
- **API Framework** : FastAPI, Uvicorn, Pydantic
- **Testing & CI/CD** : Pytest, HTTPX, GitHub Actions


## Structure du Projet

cyberguard-engine/
├── .github/
│   └── workflows/
│       └── ci.yml             # Pipeline d'intégration continue (GitHub Actions)
├── app/
│   └── main.py                # Point d'entrée de l'API FastAPI
├── data/
│   ├── raw/                   # Datasets bruts
│   └── processed/             # Jeu de données nettoyé (Train/Test split)
├── models/
│   ├── vectorizer.pkl         # Vectoriseur TF-IDF entraîné
│   └── model.pkl              # Modèle de Régression Logistique sauvegardé
├── src/
│   ├── download_data.py       # Chargement des données
│   ├── prepare_data.py        # Prétraitement et stratification
│   ├── train.py               # Entraînement et benchmark des modèles
│   ├── evaluate.py            # Calcul des métriques
│   └── predict_test.py        # Script d'inférence interactif
├── tests/
│   └── test_api.py            # Suite de 6 tests d'intégration Pytest
├── metrics.json               # Métriques d'évaluation exportées
├── requirements.txt           # Dépendances du projet
└── README.md                  # Documentation du projet


# Activer l'environnement virtuel
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Activer l'environnement virtuel
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Exécuter la suite de tests
pytest

# Lancer l'API FastAPI
uvicorn app.main:app --reload

---

### Commandes pour sauvegarder et pousser sur GitHub :

Une fois le texte coller dans `README.md` et le fichier sauvegardé (`Ctrl + S`), enregistrez tout avec Git :

```powershell
git add README.md
git commit -m "docs: ajout du README.md complet du projet"
git push origin main