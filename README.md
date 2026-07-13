# Nutrical OCR API

Serveur d'extraction nutritionnelle par OCR pour l'application Nutrical.

## Stack

- **FastAPI** — framework API
- **PaddleOCR** — moteur OCR
- **Pillow** — traitement image
- **Railway** — hébergement

## Installation locale

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer (Windows)
venv\Scripts\activate

# Activer (Mac/Linux)
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner OCR_API_KEY

# Lancer le serveur
uvicorn main:app --reload --port 8000
```

## Tester localement

```bash
curl -X POST http://localhost:8000/ocr/scan \
  -H "Authorization: Bearer votre_cle_api" \
  -F "image=@/chemin/vers/image.jpg"
```

## Variables d'environnement

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `OCR_API_KEY` | Clé API partagée avec Flutter | ✅ |
| `ENVIRONMENT` | `development` ou `production` | ❌ |
| `MAX_IMAGE_SIZE_MB` | Taille max image en Mo (défaut: 5) | ❌ |

## Format de réponse

### Succès
```json
{
  "success": true,
  "data": {
    "nom": "Flocons d'avoine",
    "kcal": 372.0,
    "proteines": 13.5,
    "glucides": 58.0,
    "lipides": 7.0,
    "fibres": 9.5
  }
}
```

### Échec détection
```json
{
  "success": false,
  "error": "NO_NUTRITION_TABLE",
  "message": "Aucun tableau nutritionnel détecté."
}
```

## Déploiement Railway

1. Push sur GitHub
2. Créer un projet Railway depuis le repo
3. Ajouter la variable `OCR_API_KEY` dans Railway → Variables
4. Railway déploie automatiquement

## Structure

```
nutrical-ocr/
├── main.py                  # Point d'entrée FastAPI
├── requirements.txt
├── Procfile                 # Configuration Railway
├── .env                     # Variables locales (non commité)
├── core/
│   ├── security.py          # Vérification Bearer token
│   ├── image_processor.py   # Validation + compression image
│   └── nutrition_parser.py  # Extraction valeurs nutritionnelles
├── routes/
│   └── ocr.py               # Route POST /ocr/scan
└── models/
    └── nutrition.py         # Modèles Pydantic
```