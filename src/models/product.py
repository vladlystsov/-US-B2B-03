from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from src.database import Base

class Product(Base):
    __tablename__ = "products"

    class Status:
        CREATED = "CREATED"
        ON_MODERATION = "ON_MODERATION"
        MODERATED = "MODERATED"
        BLOCKED = "BLOCKED"
        HARD_BLOCKED = "HARD_BLOCKED"
        
        @classmethod
        def needs_moderation_on_edit(cls, status: str) -> bool:
            """Статусы, которые при редактировании возвращаются в ON_MODERATION"""
            return status in [cls.MODERATED, cls.BLOCKED]
        
        @classmethod
        def is_editable(cls, status: str) -> bool:
            """Статусы, которые можно редактировать"""
            return status != cls.HARD_BLOCKED

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, default="")
    description = Column(Text, nullable=False)
    
    status = Column(String(50), nullable=False, default="CREATED")
    deleted = Column(Boolean, default=False, nullable=False)
    blocked = Column(Boolean, default=False, nullable=False)
    blocking_reason_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    moderator_comment = Column(Text, nullable=False, default="")
    
    images = Column(JSON, nullable=False, default=list)
    characteristics = Column(JSON, default=list)
    skus = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False, server_default=func.now())