from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class SellerProductItem(BaseModel):
    id: UUID
    title: str
    slug: str
    status: str
    category_id: UUID
    deleted: bool
    created_at: datetime
    min_price: Optional[int] = None
    cover_image: Optional[str] = None


class SellerProductsResponse(BaseModel):
    items: List[SellerProductItem] = []
    total_count: int = 0
    limit: int = 20
    offset: int = 0
