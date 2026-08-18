from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from src.database import Base
import uuid
import enum

class InvoiceStatus(str, enum.Enum):
    CREATED = "CREATED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    ACCEPTED = "ACCEPTED"
    CANCELLED = "CANCELLED"

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String(36), nullable=False, index=True)
    status = Column(SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.CREATED)
    items = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)