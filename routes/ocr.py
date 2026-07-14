import io
import logging
import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse

from core.security import verify_api_key
from core.image_processor import validate_and_compress
from core.nutrition_parser import parse_nutrition
from models.nutrition import (
    OCRSuccessResponse,
    OCRErrorResponse,
    NutritionData,
    ErrorCode,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])

# PaddleOCR initialisé une seule fois au démarrage (lourd en mémoire)
_ocr_engine = None


def get_ocr_engine():
    """Lazy init de PaddleOCR — chargé uniquement au premier appel."""
    global _ocr_engine

    if _ocr_engine is not None:
        return _ocr_engine

    try:
        from paddleocr import PaddleOCR

        logger.info("Initialisation PaddleOCR...")

        engine = PaddleOCR(
            lang="fr",
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="PP-OCRv5_mobile_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

        _ocr_engine = engine

        logger.info("PaddleOCR initialisé avec succès")

        return _ocr_engine

    except Exception as e:
        _ocr_engine = None
        logger.exception(f"Erreur initialisation PaddleOCR : {e}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Moteur OCR indisponible.",
        )


@router.post(
    "/scan",
    response_model=OCRSuccessResponse,
    responses={
        401: {"model": OCRErrorResponse, "description": "Clé API invalide"},
        413: {"model": OCRErrorResponse, "description": "Image trop grande"},
        415: {"model": OCRErrorResponse, "description": "Format non supporté"},
        422: {
            "model": OCRErrorResponse,
            "description": "Tableau nutritionnel non détecté",
        },
        500: {"model": OCRErrorResponse, "description": "Erreur serveur"},
    },
    summary="Analyser une étiquette nutritionnelle",
    description="Envoie une image d'étiquette et reçoit les valeurs nutritionnelles extraites.",
)
async def scan_nutrition_label(
    image: UploadFile = File(
        ..., description="Image de l'étiquette (JPEG/PNG/WebP, max 5Mo)"
    ),
    _: str = Depends(verify_api_key),
):
    """
    Analyse une étiquette nutritionnelle et retourne les macros extraites.

    - **Authorization** : Bearer {OCR_API_KEY} requis
    - **image** : fichier image multipart
    - Retourne les valeurs pour 100g
    """
    logger.info(
        f"Requête OCR reçue — fichier : {image.filename}, type : {image.content_type}"
    )

    # 1. Validation + compression image
    try:
        image_bytes = validate_and_compress(image)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur traitement image : {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=OCRErrorResponse(
                error=ErrorCode.INVALID_IMAGE,
                message="Impossible de traiter l'image. Vérifiez le fichier.",
            ).model_dump(),
        )

    # 2. OCR
    # Remplace les deux blocs try séparés par un seul :


    try:
        ocr = get_ocr_engine()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            results = ocr.predict(tmp_path)
            for res in results:
                logger.info(f"Textes détectés : {res['rec_texts']}")
            logger.info(f"Résultat OCR brut : {str(results)[:500]}")
            nutrition = parse_nutrition(results)
        finally:
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur OCR/parsing : {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         content=OCRErrorResponse(
                error=ErrorCode.SERVER_ERROR,
                message="Erreur lors de l'analyse de l'image.",
            ).model_dump(),
        )

    # # 3. Parsing des valeurs nutritionnelles
    # try:
    #     nutrition = parse_nutrition(results)
    # except Exception as e:
    #     logger.error(f"Erreur parsing : {e}")
    #     return JSONResponse(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         content=OCRErrorResponse(
    #             error=ErrorCode.SERVER_ERROR,
    #             message="Erreur lors de l'extraction des données.",
    #         ).model_dump(),
    #     )

    # 4. Vérification résultat
    if nutrition is None:
        logger.info("Aucun tableau nutritionnel détecté")
        return JSONResponse(
            status_code=422,
            content=OCRErrorResponse(
                error=ErrorCode.NO_NUTRITION_TABLE,
                message="Aucun tableau nutritionnel détecté. "
                "Vérifiez la qualité de l'image ou saisissez les valeurs manuellement.",
            ).model_dump(),
        )

    logger.info(
        f"OCR réussi — produit : '{nutrition.get('nom', '')}', kcal : {nutrition.get('kcal')}"
    )

    return OCRSuccessResponse(data=NutritionData(**nutrition))


@router.get(
    "/health",
    summary="Vérification santé du service",
    include_in_schema=False,
)
async def health_check():
    """Endpoint de santé — utilisé par Railway pour vérifier que le service tourne."""
    return {"status": "ok", "service": "nutrical-ocr"}
