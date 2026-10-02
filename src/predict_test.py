from pathlib import Path
import joblib

# Import des configurations du projet et de la fonction de nettoyage
from src.config import MODEL_PATH, VECTORIZER_PATH
from src.prepare_data import clean_payload

# Seuil WAF : minimum 65% de certitude pour qualifier une requête d'ATTAQUE
WAF_THRESHOLD = 0.65


def load_artifacts():
    """Charge le vectoriseur TF-IDF et le modèle retenu."""
    if not VECTORIZER_PATH.exists() or not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Artefacts introuvables dans models/. Assurez-vous d'avoir exécuté train.py d'abord."
        )

    vectorizer = joblib.load(VECTORIZER_PATH)
    model = joblib.load(MODEL_PATH)
    return vectorizer, model


def predict_payload(payload: str, vectorizer, model):
    """Prédit la classe d'une requête HTTP / payload avec le seuil WAF."""
    # Nettoyage identique à l'entraînement
    cleaned = clean_payload(payload)
    vec = vectorizer.transform([cleaned])

    if hasattr(model, "predict_proba"):
        # Probabilité d'appartenir à la classe 1 (Attaque)
        proba_attack = model.predict_proba(vec)[0][1]
        is_attack = proba_attack >= WAF_THRESHOLD
        label_str = (
            "🔴 ATTAQUE DÉTECTÉE" if is_attack else "🟢 REQUÊTE LÉGITIME"
        )
        conf_str = f" (Confiance Attaque : {proba_attack:.2%})"
    elif hasattr(model, "decision_function"):
        score = model.decision_function(vec)[0]
        is_attack = score > 0
        label_str = (
            "🔴 ATTAQUE DÉTECTÉE" if is_attack else "🟢 REQUÊTE LÉGITIME"
        )
        conf_str = f" (Score : {score:.2f})"
    else:
        pred = model.predict(vec)[0]
        label_str = "🔴 ATTAQUE DÉTECTÉE" if pred == 1 else "🟢 REQUÊTE LÉGITIME"
        conf_str = ""

    return label_str, conf_str


def run_demo_tests(vectorizer, model):
    """Exécute un test de démonstration sur des requêtes types."""
    sample_payloads = [
        # Requêtes Légitimes
        "SELECT id, name FROM users WHERE id = 12;",
        "username=john_doe&page=profile&lang=fr",
        "https://example.com/api/v1/products?category=electronics",
        # Attaques SQL Injection (SQLi)
        "' OR '1'='1' --",
        "admin' --",
        "1 UNION SELECT null, username, password FROM users--",
        # Attaques Cross-Site Scripting (XSS)
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        # Attaques Path Traversal / Command Injection
        "../../../../etc/passwd",
        "; cat /etc/passwd",
    ]

    print("\n" + "=" * 70)
    print("      TEST D'INFÉRENCE SUR ÉCHANTILLON DE DÉMONSTRATION")
    print("=" * 70)

    for payload in sample_payloads:
        label, conf = predict_payload(payload, vectorizer, model)
        print(f"Payload  : {payload}")
        print(f"Résultat : {label}{conf}")
        print("-" * 70)


def run_interactive_mode(vectorizer, model):
    """Propose une boucle interactive dans le terminal."""
    print("\n" + "=" * 70)
    print("      MODE INTERACTIF (Tapez 'exit' ou 'q' pour quitter)")
    print("=" * 70)

    while True:
        try:
            user_input = input("\nEntrez un payload à tester > ").strip()
            if user_input.lower() in ["exit", "q", "quit"]:
                print("Fin du mode interactif.")
                break
            if not user_input:
                continue

            label, conf = predict_payload(user_input, vectorizer, model)
            print(f"-> Résultat : {label}{conf}")
        except KeyboardInterrupt:
            print("\nFin de la session.")
            break


def main():
    try:
        vectorizer, model = load_artifacts()

        # 1. Test automatisé sur le jeu d'exemple
        run_demo_tests(vectorizer, model)

        # 2. Mode prompt interactif
        run_interactive_mode(vectorizer, model)

    except Exception as e:
        print(f"Erreur lors du test : {e}")


if __name__ == "__main__":
    main()