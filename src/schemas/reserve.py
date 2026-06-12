from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class ReserveItem(BaseModel):
    sku_id: str
    quantity: int = Field(..., gt=0)


class ReserveRequest(BaseModel):
    idempotency_key: str
    items: List[ReserveItem]


class ReserveResponseItem(BaseModel):
    sku_id: str
    reserved_quantity: int
    remaining_stock: int


class ReserveSuccessResponse(BaseModel):
    reserved: bool = True
    items: List[ReserveResponseItem]


class ReserveFailedItem(BaseModel):
    sku_id: str
    requested: int
    available: int
    reason: str


class ReserveFailResponse(BaseModel):
    reserved: bool = False
    failed_items: List[ReserveFailedItem]


class UnreserveItem(BaseModel):
    sku_id: str
    quantity: int = Field(..., gt=0)


class UnreserveRequest(BaseModel):
    order_id: str
    items: List[UnreserveItem]
