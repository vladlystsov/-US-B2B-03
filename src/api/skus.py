# src/api/skus.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from src.database import get_db
from src.schemas.product import SKUUpdateRequest, SKUResponse
from src.services.product_service import ProductService
from src.dependencies.auth import get_current_seller_id
from src.services.event_service import send_edited_event

router = APIRouter(prefix="/api/v1/skus", tags=["SKUs"])


@router.put("/{sku_id}", response_model=SKUResponse)
def update_sku(
    sku_id: UUID,
    sku_data: SKUUpdateRequest,
    seller_id: UUID = Depends(get_current_seller_id),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    
    updated_sku = service.update_sku(
        sku_id=str(sku_id),
        seller_id=str(seller_id),
        update_data=sku_data.model_dump(exclude_unset=True)
    )
    
    send_edited_event(
        product_id=updated_sku["product_id"],
        seller_id=str(seller_id),
        changes={"sku_updated": str(sku_id)}
    )
    
    return updated_sku