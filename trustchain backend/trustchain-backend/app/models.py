from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String

from app.database import Base


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    product_name = Column(String, index=True, nullable=False)
    batch_no = Column(String, nullable=True)
    nafdac_no = Column(String, nullable=True)
    price = Column(Float, nullable=False)

    vendor_name = Column(String, index=True, nullable=True)

    ocr_text = Column(String, nullable=True)

    score = Column(Integer, nullable=False)
    level = Column(String, nullable=False)
    flags = Column(JSON, default=list)
    verdict = Column(String, nullable=False)

    paid = Column(Boolean, default=False, nullable=False)
    squad_transaction_ref = Column(String, nullable=True, index=True)