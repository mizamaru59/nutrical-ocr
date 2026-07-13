import re
from typing import Optional


# Patterns pour détecter les valeurs nutritionnelles
# Supporte : "352 kcal", "352kJ", "13,5 g", "13.5g"
_NUMBER_PATTERN = r"(\d+[.,]?\d*)"
_UNIT_PATTERN = r"\s*(?:g|mg|kcal|kj|kJ)?"

_PATTERNS = {
    "kcal": [
        rf"{_NUMBER_PATTERN}\s*kcal",
        rf"énergie[^\d]*{_NUMBER_PATTERN}\s*kcal",
        rf"calories[^\d]*{_NUMBER_PATTERN}",
        rf"valeur énergétique[^\d]*{_NUMBER_PATTERN}\s*kcal",
        rf"energy[^\d]*{_NUMBER_PATTERN}\s*kcal",
    ],
    "proteines": [
        rf"prot[eé]ines?[^\d]*{_NUMBER_PATTERN}",
        rf"protein[^\d]*{_NUMBER_PATTERN}",
    ],
    "glucides": [
        rf"glucides?[^\d]*{_NUMBER_PATTERN}",
        rf"carbohydrate[^\d]*{_NUMBER_PATTERN}",
        rf"dont sucres?[^\d]*{_NUMBER_PATTERN}",
    ],
    "lipides": [
        rf"lipides?[^\d]*{_NUMBER_PATTERN}",
        rf"mati[eè]res?\s*grasses?[^\d]*{_NUMBER_PATTERN}",
        rf"fat[^\d]*{_NUMBER_PATTERN}",
        rf"graisses?[^\d]*{_NUMBER_PATTERN}",
    ],
    "fibres": [
        rf"fibres?\s*alimentaires?[^\d]*{_NUMBER_PATTERN}",
        rf"fibres?[^\d]*{_NUMBER_PATTERN}",
        rf"dietary\s*fibre[^\d]*{_NUMBER_PATTERN}",
        rf"fiber[^\d]*{_NUMBER_PATTERN}",
    ],
}


def _extract_value(text: str, patterns: list[str]) -> Optional[float]:
    """Tente d'extraire une valeur numérique avec les patterns donnés."""
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            raw = match.group(1).replace(",", ".")
            try:
                value = float(raw)
                # Valeur aberrante → on ignore
                if value < 0 or value > 10000:
                    continue
                return round(value, 1)
            except ValueError:
                continue
    return None


def _extract_product_name(lines: list[str]) -> str:
    """
    Tente d'extraire le nom du produit depuis les premières lignes.
    Heuristique : première ligne non nutritionnelle de plus de 3 chars.
    """
    nutrition_keywords = {
        "valeur", "énergie", "energie", "protéine", "proteine",
        "glucide", "lipide", "fibre", "sel", "sodium", "sucre",
        "graisse", "calorie", "kcal", "pour", "100g", "portion",
        "nutrition", "information", "matière", "dont",
    }

    for line in lines[:8]:
        line_clean = line.strip()
        if len(line_clean) < 3:
            continue
        line_lower = line_clean.lower()
        # Ignore les lignes contenant des mots nutritionnels
        if any(kw in line_lower for kw in nutrition_keywords):
            continue
        # Ignore les lignes qui ne contiennent que des chiffres
        if re.match(r"^[\d\s.,]+$", line_clean):
            continue
        return line_clean

    return ""


def parse_nutrition(ocr_results: list) -> Optional[dict]:
    """
    Parse les résultats PaddleOCR et extrait les valeurs nutritionnelles.

    Args:
        ocr_results: Liste de résultats PaddleOCR
                     Format: [[[box, (text, confidence)], ...], ...]

    Returns:
        dict avec les valeurs nutritionnelles ou None si non détecté.
    """
    if not ocr_results or not ocr_results[0]:
        return None

    # Extraction PaddleOCR 3.x
    lines = []
    full_text = ""

    result = ocr_results[0]

    texts = result.get("rec_texts", [])
    scores = result.get("rec_scores", [])

    for text, confidence in zip(texts, scores):
        text = str(text).strip()

        if confidence >= 0.5 and text:
            lines.append(text)
            full_text += text + "\n"

    if not full_text.strip():
        return None

    # Extraction des valeurs
    kcal = _extract_value(full_text, _PATTERNS["kcal"])
    proteines = _extract_value(full_text, _PATTERNS["proteines"])
    glucides = _extract_value(full_text, _PATTERNS["glucides"])
    lipides = _extract_value(full_text, _PATTERNS["lipides"])
    fibres = _extract_value(full_text, _PATTERNS["fibres"])
    nom = _extract_product_name(lines)

    # On considère la détection réussie si on a au moins kcal + une macro
    macros_detected = sum(
        v is not None for v in [proteines, glucides, lipides]
    )
    if kcal is None and macros_detected < 2:
        return None

    return {
        "nom": nom,
        "kcal": kcal or 0.0,
        "proteines": proteines or 0.0,
        "glucides": glucides or 0.0,
        "lipides": lipides or 0.0,
        "fibres": fibres or 0.0,
    }