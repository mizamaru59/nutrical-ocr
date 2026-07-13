import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.ocr import router as ocr_router

# Chargement des variables d'environnement
load_dotenv()

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie de l'application — démarrage et arrêt propre."""
    logger.info("Démarrage du serveur Nutrical OCR")
    logger.info(f"Environnement : {os.getenv('ENVIRONMENT', 'development')}")

    # Vérification clé API configurée
    api_key = os.getenv("OCR_API_KEY", "")
    if not api_key or api_key == "ntr_change_this_to_a_random_secret_key":
        logger.warning("⚠️  OCR_API_KEY non configurée ou valeur par défaut — à changer en production")

    yield

    logger.info("Arrêt du serveur Nutrical OCR")


# Initialisation FastAPI
app = FastAPI(
    title="Nutrical OCR API",
    description="Serveur d'extraction nutritionnelle par OCR pour l'application Nutrical.",
    version="1.0.0",
    lifespan=lifespan,
    # En production, désactiver la doc publique
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
)

# CORS — autorise uniquement les requêtes de l'app mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mobile → pas de restriction d'origine
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routes
app.include_router(ocr_router)


# Gestion globale des erreurs non catchées
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Erreur non gérée : {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "SERVER_ERROR",
            "message": "Une erreur inattendue est survenue.",
        },
    )


# Point d'entrée racine
@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Nutrical OCR API",
        "version": "1.0.0",
        "status": "running",
    }