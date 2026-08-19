from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/public/products", tags=["Public Catalog"])
sku_router = APIRouter(prefix="/api/v1/public/skus", tags=["Public Catalog"])


class BatchProductsRequest(BaseModel):
    product_ids: list[str] = Field(..., max_length=100)


def require_b2c_service_key(x_service_key: Optional[str] = Header(None)) -> None:
    if x_service_key != settings.B2C_TO_B2B_KEY:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or missing X-Service-Key"},
        )


@router.get("")
def list_public_products(
    db: Session = Depends(get_db),
    _: None = Depends(require_b2c_service_key),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category_id: Optional[str] = None,
    search: Optional[str] = Query(None, min_length=3),
    sort: Optional[str] = None,
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    seller_id: Optional[str] = None,
):
    service = ProductService(db)
    products, total = service.get_catalog_products(
        limit=limit,
        offset=offset,
        category=category_id,
        search=search,
        sort=sort,
        price_min=min_price,
        price_max=max_price,
        seller_id=seller_id,
    )
    return {
        "items": [service.format_public_short(product) for product in products],
        "total_count": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/batch")
def batch_public_products(
    payload: BatchProductsRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_b2c_service_key),
):
    service = ProductService(db)
    products, _ = service.get_catalog_products(limit=len(payload.product_ids), ids=payload.product_ids)
    by_id = {str(product.id): product for product in products}
    return [service.format_public_product(by_id[product_id]) for product_id in payload.product_ids if product_id in by_id]


@router.get("/{product_id}")
def get_public_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_b2c_service_key),
):
    product = ProductService(db).get_public_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Product not found"})
    return product


@router.get("/{product_id}/similar")
def get_public_similar_products(
    product_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_b2c_service_key),
    limit: int = Query(10, ge=1, le=50),
):
    service = ProductService(db)
    product = service.get_public_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Product not found"})
    products, _ = service.get_catalog_products(limit=limit + 1, category=product["category_id"])
    return [service.format_public_short(item) for item in products if str(item.id) != str(product_id)][:limit]


@sku_router.get("/{sku_id}")
def get_public_sku(
    sku_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_b2c_service_key),
):
    sku = ProductService(db).get_public_sku(sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "SKU not found"})
    return sku
