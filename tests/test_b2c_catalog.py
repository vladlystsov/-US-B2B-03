import pytest
from uuid import uuid4
from datetime import datetime

from src.models.product import Product
from src.config import settings


class TestB2CCatalog:

    def test_catalog_returns_moderated_in_stock_products(self, client, db_session):
        """MODERATED + deleted=false + active_quantity>0 → visible in catalog"""
        product = Product(
            id=str(uuid4()),
            seller_id=str(uuid4()),
            category_id=str(uuid4()),
            title="iPhone 15",
            slug="iphone-15",
            description="Smartphone",
            status=Product.Status.MODERATED,
            deleted=False,
            blocked=False,
            images=[{"url": "/s3/front.jpg", "ordering": 0}],
            characteristics=[{"name": "Brand", "value": "Apple"}],
            skus=[{
                "id": str(uuid4()),
                "sku_code": "SKU001",
                "price": 100000,
                "active_quantity": 5,
                "reserved_quantity": 2
            }]
        )
        db_session.add(product)
        db_session.commit()

        response = client.get(
            "/api/v1/public/products",
            headers={"X-Service-Key": settings.B2C_SERVICE_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        titles = [p["title"] for p in data["items"]]
        assert "iPhone 15" in titles

    def test_catalog_excludes_hard_blocked(self, client, db_session):
        """HARD_BLOCKED product → not in catalog"""
        product = Product(
            id=str(uuid4()),
            seller_id=str(uuid4()),
            category_id=str(uuid4()),
            title="Banned Product",
            slug="banned-product",
            description="Bad",
            status=Product.Status.HARD_BLOCKED,
            deleted=False,
            blocked=True,
            images=[{"url": "/s3/banned.jpg", "ordering": 0}],
            characteristics=[],
            skus=[{
                "id": str(uuid4()),
                "sku_code": "SKU002",
                "price": 10000,
                "active_quantity": 10
            }]
        )
        db_session.add(product)
        db_session.commit()

        response = client.get(
            "/api/v1/public/products",
            headers={"X-Service-Key": settings.B2C_SERVICE_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        titles = [p["title"] for p in data["items"]]
        assert "Banned Product" not in titles

    def test_catalog_missing_service_key_returns_401(self, client, db_session):
        """No X-Service-Key → 401"""
        response = client.get("/api/v1/public/products")

        assert response.status_code == 401

    def test_catalog_response_has_no_cost_price(self, client, db_session):
        """B2C response must NOT contain cost_price or reserved_quantity"""
        product = Product(
            id=str(uuid4()),
            seller_id=str(uuid4()),
            category_id=str(uuid4()),
            title="Secret Product",
            slug="secret-product",
            description="Has secrets",
            status=Product.Status.MODERATED,
            deleted=False,
            blocked=False,
            images=[{"url": "/s3/secret.jpg", "ordering": 0}],
            characteristics=[],
            skus=[{
                "id": str(uuid4()),
                "sku_code": "SKU003",
                "price": 50000,
                "cost_price": 25000,
                "active_quantity": 3,
                "reserved_quantity": 7
            }]
        )
        db_session.add(product)
        db_session.commit()

        response = client.get(
            "/api/v1/public/products",
            headers={"X-Service-Key": settings.B2C_SERVICE_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        item = next(item for item in data["items"] if item["title"] == "Secret Product")
        assert item["min_price"] == 50000
        assert "cost_price" not in item
        assert "reserved_quantity" not in item

        detail = client.post(
            "/api/v1/public/products/batch",
            json={"product_ids": [str(product.id)]},
            headers={"X-Service-Key": settings.B2C_TO_B2B_KEY},
        )
        assert detail.status_code == 200
        sku = detail.json()[0]["skus"][0]
        assert "cost_price" not in sku
        assert "reserved_quantity" not in sku

    def test_batch_ids_returns_visible_subset(self, client, db_session):
        """?ids= returns only visible products, no 404 for hidden ones"""
        seller_id = str(uuid4())
        cat_id = str(uuid4())

        visible_product = Product(
            id=str(uuid4()),
            seller_id=seller_id,
            category_id=cat_id,
            title="Visible Product",
            slug="visible",
            description="Visible",
            status=Product.Status.MODERATED,
            deleted=False,
            blocked=False,
            images=[{"url": "/s3/vis.jpg", "ordering": 0}],
            characteristics=[],
            skus=[{
                "id": str(uuid4()),
                "sku_code": "SKU004",
                "price": 10000,
                "active_quantity": 1
            }]
        )
        hidden_product = Product(
            id=str(uuid4()),
            seller_id=seller_id,
            category_id=cat_id,
            title="Hidden Product",
            slug="hidden",
            description="Hidden",
            status=Product.Status.CREATED,
            deleted=False,
            blocked=False,
            images=[{"url": "/s3/hid.jpg", "ordering": 0}],
            characteristics=[],
            skus=[{
                "id": str(uuid4()),
                "sku_code": "SKU005",
                "price": 20000,
                "active_quantity": 1
            }]
        )
        deleted_product = Product(
            id=str(uuid4()),
            seller_id=seller_id,
            category_id=cat_id,
            title="Deleted Product",
            slug="deleted",
            description="Deleted",
            status=Product.Status.MODERATED,
            deleted=True,
            blocked=False,
            images=[],
            characteristics=[],
            skus=[]
        )
        db_session.add_all([visible_product, hidden_product, deleted_product])
        db_session.commit()

        response = client.post(
            "/api/v1/public/products/batch",
            json={"product_ids": [str(visible_product.id), str(hidden_product.id), str(deleted_product.id)]},
            headers={"X-Service-Key": settings.B2C_TO_B2B_KEY},
        )

        assert response.status_code == 200
        returned_ids = [item["id"] for item in response.json()]
        assert str(visible_product.id) in returned_ids
        assert str(hidden_product.id) not in returned_ids
        assert str(deleted_product.id) not in returned_ids


def test_public_catalog_list_includes_characteristics_and_public_skus(client, db_session):
    product = Product(
        id=str(uuid4()),
        seller_id=str(uuid4()),
        category_id=str(uuid4()),
        title="Rich public product",
        slug="rich-public-product",
        description="Complete public catalog representation",
        status=Product.Status.MODERATED,
        deleted=False,
        blocked=False,
        images=[{"url": "/s3/rich.jpg", "ordering": 0}],
        characteristics=[{"name": "brand", "value": "Neo"}],
        skus=[{
            "id": str(uuid4()),
            "sku_code": "RICH-1",
            "price": 12000,
            "active_quantity": 2,
            "cost_price": 5000,
            "reserved_quantity": 1,
        }],
    )
    db_session.add(product)
    db_session.commit()

    response = client.get("/api/v1/public/products", headers={"X-Service-Key": settings.B2C_TO_B2B_KEY})
    item = next(item for item in response.json()["items"] if item["id"] == product.id)

    assert response.status_code == 200
    assert set(item) >= {"id", "title", "slug", "status", "category_id", "min_price", "created_at"}
    assert "description" not in item
    assert "characteristics" not in item
    assert "skus" not in item

    batch = client.post(
        "/api/v1/public/products/batch",
        json={"product_ids": [product.id]},
        headers={"X-Service-Key": settings.B2C_TO_B2B_KEY},
    )
    full_item = batch.json()[0]
    assert full_item["description"] == product.description
    assert full_item["characteristics"] == [{"name": "brand", "value": "Neo"}]
    assert full_item["skus"][0]["id"] == product.skus[0]["id"]
    assert "cost_price" not in full_item["skus"][0]
    assert "reserved_quantity" not in full_item["skus"][0]


def test_public_catalog_forwards_dynamic_characteristic_filter(client, db_session):
    seller_id = str(uuid4())
    common = {
        "seller_id": seller_id,
        "category_id": str(uuid4()),
        "description": "Filtered",
        "status": Product.Status.MODERATED,
        "deleted": False,
        "blocked": False,
        "images": [],
        "skus": [{"id": str(uuid4()), "sku_code": "FILTER", "price": 1000, "active_quantity": 1}],
    }
    matching = Product(id=str(uuid4()), title="Neo brand", slug="neo-brand", characteristics=[{"name": "brand", "value": "Neo"}], **common)
    other = Product(id=str(uuid4()), title="Other brand", slug="other-brand", characteristics=[{"name": "brand", "value": "Other"}], **common)
    db_session.add_all([matching, other])
    db_session.commit()

    response = client.get(
        "/api/v1/public/products?filters[brand]=Neo",
        headers={"X-Service-Key": settings.B2C_TO_B2B_KEY},
    )
    ids = {item["id"] for item in response.json()["items"]}

    assert matching.id in ids
    assert other.id not in ids


def test_similar_products_fallback_to_parent_category(client, db_session):
    from src.models.category import Category

    root = Category(id=str(uuid4()), name="Root", slug="root", parent_id=None, is_active=True)
    child = Category(id=str(uuid4()), name="Child", slug="child", parent_id=root.id, is_active=True)
    current = Product(
        id=str(uuid4()), seller_id=str(uuid4()), category_id=child.id, title="Current", slug="current", description="Current",
        status=Product.Status.MODERATED, deleted=False, blocked=False, images=[], characteristics=[],
        skus=[{"id": str(uuid4()), "sku_code": "CURRENT", "price": 1000, "active_quantity": 1}],
    )
    parent_candidate = Product(
        id=str(uuid4()), seller_id=str(uuid4()), category_id=root.id, title="Parent candidate", slug="parent-candidate", description="Fallback",
        status=Product.Status.MODERATED, deleted=False, blocked=False, images=[], characteristics=[],
        skus=[{"id": str(uuid4()), "sku_code": "PARENT", "price": 1200, "active_quantity": 1}],
    )
    db_session.add_all([root, child, current, parent_candidate])
    db_session.commit()

    response = client.get(
        f"/api/v1/public/products/{current.id}/similar?limit=8",
        headers={"X-Service-Key": settings.B2C_TO_B2B_KEY},
    )

    assert response.status_code == 200
    assert parent_candidate.id in {item["id"] for item in response.json()}
    assert current.id not in {item["id"] for item in response.json()}


def test_public_catalog_accepts_multiple_values_for_one_attribute_filter(client, db_session):
    common = {
        "seller_id": str(uuid4()),
        "category_id": str(uuid4()),
        "description": "Repeated filter values",
        "status": Product.Status.MODERATED,
        "deleted": False,
        "blocked": False,
        "images": [],
        "skus": [{"id": str(uuid4()), "sku_code": "MULTI", "price": 1000, "active_quantity": 1}],
    }
    apple = Product(id=str(uuid4()), title="Apple", slug="apple", characteristics=[{"name": "brand", "value": "apple"}], **common)
    samsung = Product(id=str(uuid4()), title="Samsung", slug="samsung", characteristics=[{"name": "brand", "value": "samsung"}], **common)
    other = Product(id=str(uuid4()), title="Other", slug="other", characteristics=[{"name": "brand", "value": "other"}], **common)
    db_session.add_all([apple, samsung, other])
    db_session.commit()

    response = client.get(
        "/api/v1/public/products?filters[brand]=apple&filters[brand]=samsung",
        headers={"X-Service-Key": settings.B2C_TO_B2B_KEY},
    )
    ids = {item["id"] for item in response.json()["items"]}

    assert apple.id in ids
    assert samsung.id in ids
    assert other.id not in ids
