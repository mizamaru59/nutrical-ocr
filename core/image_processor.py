import io
import os
from PIL import Image
from fastapi import HTTPException, UploadFile, status

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_DIMENSION = 2048  # pixels


def validate_and_compress(file: UploadFile) -> bytes:
    """
    Valide l'image uploadée et la compresse si nécessaire.
    Retourne les bytes de l'image prête pour PaddleOCR.
    """
    # Vérification type MIME
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Format non supporté : {file.content_type}. "
                   f"Formats acceptés : JPEG, PNG, WebP.",
        )

    # Lecture des bytes
    image_bytes = file.file.read()

    # Vérification taille
    max_size_mb = float(os.getenv("MAX_IMAGE_SIZE_MB", "5"))
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(image_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image trop volumineuse. "
                   f"Taille maximale : {max_size_mb} Mo.",
        )

    # Ouverture et redimensionnement si nécessaire
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de lire l'image. Fichier corrompu.",
        )

    # Conversion en RGB si nécessaire (ex: PNG avec transparence)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    # Redimensionnement si trop grande
    if max(image.size) > MAX_DIMENSION:
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    # Recompression en JPEG pour uniformité
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)
    return output.getvalue()