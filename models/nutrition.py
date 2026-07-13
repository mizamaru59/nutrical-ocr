from pydantic import BaseModel, Field
from typing import Optional


class NutritionData(BaseModel):
    """Valeurs nutritionnelles extraites pour 100g."""
    nom: str = Field(default="", description="Nom du produit détecté")
    kcal: float = Field(default=0.0, ge=0, description="Calories pour 100g")
    proteines: float = Field(default=0.0, ge=0, description="Protéines en g pour 100g")
    glucides: float = Field(default=0.0, ge=0, description="Glucides en g pour 100g")
    lipides: float = Field(default=0.0, ge=0, description="Lipides en g pour 100g")
    fibres: float = Field(default=0.0, ge=0, description="Fibres en g pour 100g")


class OCRSuccessResponse(BaseModel):
    """Réponse en cas de succès de l'OCR."""
    success: bool = True
    data: NutritionData


class OCRErrorResponse(BaseModel):
    """Réponse en cas d'échec de l'OCR."""
    success: bool = False
    error: str
    message: str


# Codes d'erreur standardisés
class ErrorCode:
    NO_NUTRITION_TABLE = "NO_NUTRITION_TABLE"
    INVALID_IMAGE = "INVALID_IMAGE"
    SERVER_ERROR = "SERVER_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"