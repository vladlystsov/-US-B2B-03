from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.schemas.product import CatalogResponse
from src.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/public/products", tags=["Public Catalog"])


def require_b2c_service_key(x_service_key: Optional[str] = Header(None)) -> None:
    if x_service_key != settings.B2C_SERVICE_KEY:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or missing X-Service-Key"},
        )


@router.get("", response_model=CatalogResponse)
def list_public_products(
    db: Session = Depends(get_db),
    _: None = Depends(require_b2c_service_key),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    ids: Optional[str] = None,
):
    """Public B2C catalog: moderated, non-deleted products with stock only."""
    id_list = [item.strip() for item in ids.split(",") if item.strip()] if ids else None
    service = ProductService(db)
    products, total = service.get_catalog_products(
        limit=limit,
        offset=offset,
        category=category,
        search=search,
        sort=sort,
        ids=id_list,
    )
    return CatalogResponse(
        items=[service._format_for_catalog(product) for product in products],
        total_count=total,
        limit=limit,
        offset=offset,
    )
