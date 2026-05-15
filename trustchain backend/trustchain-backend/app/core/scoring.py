import re
from typing import Dict, List

from pydantic import BaseModel

from app.core.config import settings


# =========================================================
# NAFDAC VALIDATION
# =========================================================

def is_valid_nafdac(nafdac_no: str) -> bool:
    if not nafdac_no:
        return False

    normalized = nafdac_no.strip().upper()

    try:
        from app.core.nafdac_list import VALID_NAFDAC

        if normalized in VALID_NAFDAC:
            return True

    except Exception:
        pass

    # fallback regex validation
    pattern = re.compile(r"^[A-Z0-9]{2,}[-/][A-Z0-9]+$")

    return bool(pattern.match(normalized))


# =========================================================
# RESPONSE MODEL
# =========================================================

class RiskResult(BaseModel):
    score: int
    level: str
    flags: List[str]
    verdict: str


# =========================================================
# CORE SCORING ENGINE
# =========================================================

def calculate_trust_score(
    product: Dict,
    vendor: Dict
) -> RiskResult:

    score = 100
    flags: List[str] = []

    # =====================================================
    # 1. NAFDAC VALIDATION
    # =====================================================

    nafdac_no = str(product.get("nafdac_no", "") or "")

    if not is_valid_nafdac(nafdac_no):
        score -= 35
        flags.append(
            "Invalid or unverified NAFDAC registration"
        )

    # =====================================================
    # 2. PRICE ANALYSIS
    # =====================================================

    market_avg = float(
        product.get(
            "market_avg",
            settings.MARKET_AVG
        ) or 0
    )

    price = float(
        product.get("price", 0.0) or 0.0
    )

    if market_avg > 0:

        if price < (market_avg * 0.6):
            score -= 20
            flags.append(
                "Price significantly below market average"
            )

        elif price > (market_avg * 1.8):
            score -= 10
            flags.append(
                "Price unusually high"
            )

    # =====================================================
    # 3. EXPIRY ANALYSIS
    # =====================================================

    if product.get("expiry_status") == "expired":
        score -= 40
        flags.append(
            "Product is past expiration date"
        )

    # =====================================================
    # 4. VENDOR ANALYSIS
    # =====================================================

    if vendor.get("years_in_business", 0) < 1:
        score -= 15
        flags.append(
            "Vendor has less than 1 year of verified history"
        )

    if vendor.get("complaint_count", 0) > 2:
        score -= 25
        flags.append(
            "Multiple unresolved complaints detected"
        )

    if not vendor.get("is_cac_registered"):
        score -= 20
        flags.append(
            "Vendor not found in CAC registry"
        )

    # =====================================================
    # 5. OCR LABEL VALIDATION
    # =====================================================

    ocr_text = str(
        product.get("ocr_text", "")
    ).lower()

    product_name = str(
        product.get("product_name", "")
    ).lower()

    if ocr_text and product_name:

        if product_name not in ocr_text:
            score -= 10
            flags.append(
                "OCR label mismatch detected"
            )

    # =====================================================
    # FINAL SCORE NORMALIZATION
    # =====================================================

    score = max(0, min(score, 100))

    # =====================================================
    # RISK CLASSIFICATION
    # =====================================================

    if score >= 80:
        level = "LOW"
        verdict = "Likely Genuine"

    elif score >= 60:
        level = "MEDIUM"
        verdict = "Proceed with Caution"

    else:
        level = "HIGH"
        verdict = "High Risk / Possible Fraud"

    # =====================================================
    # RETURN RESULT
    # =====================================================

    return RiskResult(
        score=score,
        level=level,
        flags=flags,
        verdict=verdict,
    )