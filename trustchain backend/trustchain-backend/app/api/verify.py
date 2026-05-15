from __future__ import annotations

import os
import tempfile
from dataclasses import asdict

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.scoring import calculate_trust_score
from app.database import get_db
from app.models import Verification
from app.services.ocr import extract_label_text


router = APIRouter()


@router.post("/run")
async def run_verification(
    product_name: str = Form(...),
    batch_no: str = Form(""),
    nafdac_no: str = Form(""),
    price: float = Form(...),
    vendor_name: str = Form(""),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # =====================================================
    # VALIDATION
    # =====================================================

    if price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than zero.",
        )

    if image.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG and PNG images are allowed.",
        )

    contents = await image.read()

    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image exceeds 5MB upload limit.",
        )

    suffix = os.path.splitext(
        image.filename or ""
    )[1] or ".png"

    temp_path = None

    try:

        # =================================================
        # SAVE TEMP FILE
        # =================================================

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(contents)
            temp_path = temp_file.name

        # =================================================
        # OCR EXTRACTION
        # =================================================

        ocr_text = extract_label_text(temp_path)

        # =================================================
        # PRODUCT DATA
        # =================================================

        product_data = {
            "product_name": product_name,
            "batch_no": batch_no,
            "nafdac_no": nafdac_no,
            "price": price,
            "market_avg": settings.MARKET_AVG,
            "ocr_text": ocr_text,
            "expiry_status": "active",
        }

        # =================================================
        # VENDOR DATA
        # =================================================

        vendor_data = {
            "vendor_name": vendor_name,
            "years_in_business": 2,
            "complaint_count": 0,
            "is_cac_registered": True,
        }

        # =================================================
        # TRUST ANALYSIS
        # =================================================

        analysis = calculate_trust_score(
            product_data,
            vendor_data,
        )

        # =================================================
        # PAYMENT CONTROL LOGIC
        # =================================================

        payment_allowed = analysis.score >= 60

        payment_status = (
            "allowed"
            if payment_allowed
            else "paused"
        )

        # =================================================
        # PAYMENT AMOUNT
        # =================================================

        payment_amount = int(price)

        # Squad uses kobo
        payment_amount_kobo = payment_amount * 100

        # =================================================
        # SAVE VERIFICATION
        # =================================================

        verification = Verification(
            product_name=product_name,
            batch_no=batch_no,
            nafdac_no=nafdac_no,
            price=price,
            vendor_name=vendor_name,
            ocr_text=ocr_text,
            score=analysis.score,
            level=analysis.level,
            flags=analysis.flags,
            verdict=analysis.verdict,
            paid=False,
        )

        db.add(verification)
        db.commit()
        db.refresh(verification)

        # =================================================
        # RESPONSE
        # =================================================

        return {
            "id": f"TRC-{verification.id}",
            "verification_id": verification.id,

            # =================================================
            # PAYMENT DECISION
            # =================================================

            "payment_allowed": payment_allowed,
            "payment_status": payment_status,

            # =================================================
            # ACTUAL PRODUCT PAYMENT
            # =================================================

            "payment_amount": payment_amount,
            "payment_amount_kobo": payment_amount_kobo,
            "currency": "NGN",

            # =================================================
            # PRODUCT
            # =================================================

            "product": {
                "name": product_name,
                "batch_no": batch_no,
                "nafdac_no": nafdac_no,
                "price": price,
                "ocr_text": ocr_text,
            },

            # =================================================
            # VENDOR
            # =================================================

            "vendor": {
                "name": vendor_name,
            },

            # =================================================
            # ANALYSIS
            # =================================================

            "analysis": (
                analysis.model_dump()
                if hasattr(analysis, "model_dump")
                else asdict(analysis)
            ),
        }

    finally:

        # =================================================
        # CLEAN TEMP FILE
        # =================================================

        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)

            except OSError:
                pass