from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class FieldReport(BaseModel):
    field_name: str
    comment: str


class BlockingReason(BaseModel):
    id: str
    title: str
    comment: str


class ModerationEventRequest(BaseModel):
    idempotency_key: str
    product_id: str
    status: Literal["MODERATED", "BLOCKED"]
    hard_block: Optional[bool] = False
    blocking_reason: Optional[BlockingReason] = None
    field_reports: Optional[List[FieldReport]] = None
