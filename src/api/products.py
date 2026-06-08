from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from src.database import get_db
from src.schemas.product import ProductCreateRequest, ProductResponse
from src.services.product_service import ProductService
from src.dependencies.auth import get_current_seller_id

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    product_data: ProductCreateRequest,
    seller_id: UUID = Depends(get_current_seller_id),
    db: Session = Depends(get_db)
):
    if not product_data.images:
        raise HTTPException(400, {"code": "INVALID_REQUEST", "message": "At least one image is required"})
    
    service = ProductService(db)
    product = service.create_product(seller_id, product_data)
    return product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_data: ProductUpdateRequest,
    seller_id: UUID = Depends(get_current_seller_id),
    db: Session = Depends(get_db)
):
    """
    PUT /api/v1/products/{id}
    Редактирование товара с переходом в ON_MODERATION
    """
    service = ProductService(db)
    
    # Обновляем товар
    updated_product = service.update_product(
        product_id=product_id,
        seller_id=seller_id,
        update_data=product_data.model_dump(exclude_unset=True)
    )
    
    # Отправляем событие в Moderation Service
    from src.services.event_service import send_edited_event
    send_edited_event(
        product_id=updated_product.id,
        seller_id=seller_id,
        changes=product_data.model_dump(exclude_unset=True)
    )
    
    return updated_product