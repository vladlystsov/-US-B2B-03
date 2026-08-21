from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from src.models.product import Product
from src.services.product_service import ProductService


def _product(seller_id: str, status: str = "MODERATED") -> Product:
    return Product(
        id=str(uuid4()),
        seller_id=seller_id,
        category_id=str(uuid4()),
        title="Round two product",
        slug=f"round-two-{uuid4()}",
        description="Public catalog test product",
        status=status,
        images=[],
        characteristics=[],
        skus=[],
    )


def test_public_sku_image_has_contract_uuid_id(db_session, valid_jwt_with_fixed_id):
    _, seller_id = valid_jwt_with_fixed_id
    product = _product(seller_id)
    sku = {
        "id": str(uuid4()),
        "sku_code": "SKU-IMAGE",
        "price": 1000,
        "active_quantity": 2,
        "image": "https://example.test/sku.jpg",
    }
    data = ProductService(db_session)._public_sku(product, sku)

    assert data["images"] == [
        {
            "id": data["images"][0]["id"],
            "url": "https://example.test/sku.jpg",
            "ordering": 0,
        }
    ]
    UUID(data["images"][0]["id"])


def test_hard_blocked_product_cannot_be_deleted(db_session, valid_jwt_with_fixed_id):
    _, seller_id = valid_jwt_with_fixed_id
    product = _product(seller_id, status=Product.Status.HARD_BLOCKED)
    db_session.add(product)
    db_session.commit()

    with pytest.raises(HTTPException) as error:
        ProductService(db_session).delete_product(product.id, seller_id)

    assert error.value.status_code == 403
    assert error.value.detail["code"] == "HARD_BLOCKED"



def test_public_sku_characteristics_have_complete_contract_shape(db_session, valid_jwt_with_fixed_id):
    _, seller_id = valid_jwt_with_fixed_id
    product = _product(seller_id)
    sku = {
        "id": str(uuid4()),
        "sku_code": "SKU-CHARACTERISTIC",
        "price": 1000,
        "active_quantity": 2,
        "characteristics": [{"name": "memory", "value": "256"}],
    }

    first = ProductService(db_session)._public_sku(product, sku)
    second = ProductService(db_session)._public_sku(product, sku)

    assert first["characteristics"] == second["characteristics"]
    characteristic = first["characteristics"][0]
    assert characteristic["name"] == "memory"
    assert characteristic["value"] == "256"
    UUID(characteristic["id"])
