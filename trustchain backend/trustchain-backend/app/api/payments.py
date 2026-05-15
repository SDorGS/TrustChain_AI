from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import Verification

router = APIRouter()


# =========================================================
# REQUEST MODEL
# =========================================================

class PaymentRequest(BaseModel):
    email: str
    amount: int  # amount in NAIRA
    verification_id: int


# =========================================================
# INITIATE PAYMENT
# =========================================================

@router.post("/initiate")
async def initiate_payment(req: PaymentRequest):

    # =====================================================
    # VALIDATE CONFIG
    # =====================================================

    if not settings.SQUAD_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Squad API key missing",
        )

    # =====================================================
    # VALIDATE INPUT
    # =====================================================

    if req.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment amount",
        )

    # =====================================================
    # CONVERT NAIRA -> KOBO
    # =====================================================

    # Squad expects amount in kobo
    amount_kobo = int(req.amount * 100)

    # =====================================================
    # HEADERS
    # =====================================================

    headers = {
        "Authorization": f"Bearer {settings.SQUAD_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    # =====================================================
    # PAYLOAD
    # =====================================================

    payload = {

        # IMPORTANT:
        # send kobo to Squad
        "amount": amount_kobo,

        "email": req.email,

        "currency": "NGN",

        # inline checkout
        "initiate_type": "inline",

        "metadata": {
            "verification_id": req.verification_id,
        },
    }

    # =====================================================
    # SEND TO SQUAD
    # =====================================================

    try:

        async with httpx.AsyncClient(
            timeout=30
        ) as client:

            response = await client.post(
                f"{settings.SQUAD_BASE_URL}/transaction/initiate",
                json=payload,
                headers=headers,
            )

    except httpx.RequestError:

        raise HTTPException(
            status_code=500,
            detail="Unable to connect to Squad API",
        )

    # =====================================================
    # HANDLE FAILED RESPONSE
    # =====================================================

    if response.status_code not in (200, 201):

        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    # =====================================================
    # SUCCESS
    # =====================================================

    return response.json()


# =========================================================
# WEBHOOK
# =========================================================

@router.post("/webhook")
async def squad_webhook(
    request: Request,
    db: Session = Depends(get_db),
):

    # =====================================================
    # PARSE PAYLOAD
    # =====================================================

    payload: Dict[str, Any] = await request.json()

    event = (
        payload.get("Event")
        or payload.get("event")
    )

    body = (
        payload.get("Body")
        or payload.get("body")
        or payload.get("data")
        or {}
    )

    meta = (
        body.get("meta")
        or body.get("metadata")
        or {}
    )

    # =====================================================
    # EXTRACT VERIFICATION ID
    # =====================================================

    verification_id: Optional[int] = None

    raw_verification_id = meta.get(
        "verification_id"
    )

    if raw_verification_id is not None:

        try:
            verification_id = int(
                raw_verification_id
            )

        except Exception:
            verification_id = None

    # =====================================================
    # TRANSACTION STATUS
    # =====================================================

    transaction_status = (
        body.get("transaction_status")
        or body.get("status")
        or payload.get("status")
    )

    transaction_ref = (
        body.get("transaction_ref")
        or body.get("reference")
        or body.get("transaction_reference")
        or payload.get("reference")
    )

    # =====================================================
    # SUCCESSFUL PAYMENT
    # =====================================================

    is_successful = (
        event == "charge_successful"
        or str(transaction_status).lower()
        in {
            "success",
            "successful",
            "paid",
        }
    )

    if is_successful and verification_id:

        verification = (
            db.query(Verification)
            .get(verification_id)
        )

        if verification:

            verification.paid = True

            if transaction_ref:
                verification.squad_transaction_ref = str(
                    transaction_ref
                )

            db.commit()

    # =====================================================
    # ACKNOWLEDGE WEBHOOK
    # =====================================================

    return {
        "received": True
    }