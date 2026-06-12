from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from src.database import get_db
from src.schemas.product import (
    ProductCreateRequest, 
    ProductResponse, 
    ProductUpdateRequest
)
from src.services.product_service import ProductService
from src.dependencies.auth import get_current_seller_id
from typing import List

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
    product = service.create_product(str(seller_id), product_data)
    return product

@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_data: ProductUpdateRequest,
    seller_id: UUID = Depends(get_current_seller_id),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    
    updated_product = service.update_product(
        product_id=str(product_id),
        seller_id=str(seller_id),
        update_data=product_data.model_dump(exclude_unset=True)
    )
    
    from src.services.event_service import send_edited_event
    send_edited_event(
        product_id=updated_product.id,
        seller_id=str(seller_id),
        changes=product_data.model_dump(exclude_unset=True)
    )
    
    return updated_product

@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: UUID,
    seller_id: UUID = Depends(get_current_seller_id),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    service.delete_product(product_id=str(product_id), seller_id=str(seller_id))
    return None

@router.get("/", response_model=list[ProductResponse])
def get_products(
    seller_id: UUID = Depends(get_current_seller_id),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    service = ProductService(db)
    products = service.get_seller_products(str(seller_id), skip=skip, limit=limit)
    return products