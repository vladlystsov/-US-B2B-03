# tests/test_product_delete.py
import pytest
from uuid import uuid4
from unittest.mock import patch

from src.models.product import Product


class TestProductDelete:
    
    def test_delete_sets_deleted_true(self, client, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=str(uuid4()),
            seller_id=str(seller_id),
            category_id=str(uuid4()),
            title="Test Product",
            description="Test Description",
            status="MODERATED",
            deleted=False,
            images=[],
            slug="test-product"
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/products/{product.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        db_session.refresh(product)
        assert product.deleted == True
    
    def test_delete_emits_event_to_moderation(self, client, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=str(uuid4()),
            seller_id=str(seller_id),
            category_id=str(uuid4()),
            title="Test Product",
            description="Test Description",
            status="MODERATED",
            deleted=False,
            images=[],
            slug="test-product"
        )
        db_session.add(product)
        db_session.commit()
        
        with patch('src.services.event_service.send_deleted_event') as mock_event:
            response = client.delete(
                f"/api/v1/products/{product.id}",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 204
        mock_event.assert_called_once_with(
            product_id=product.id,
            seller_id=seller_id
        )
    
    def test_delete_emits_product_deleted_to_b2c(self, client, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        sku_id = str(uuid4())
        product = Product(
            id=str(uuid4()),
            seller_id=str(seller_id),
            category_id=str(uuid4()),
            title="Test Product",
            description="Test Description",
            status="MODERATED",
            deleted=False,
            images=[],
            slug="test-product",
            skus=[{"id": sku_id, "sku_code": "TEST001", "price": 100}]
        )
        db_session.add(product)
        db_session.commit()
        
        with patch('src.services.event_service.send_product_deleted_to_b2c') as mock_event:
            response = client.delete(
                f"/api/v1/products/{product.id}",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 204
        mock_event.assert_called_once_with(
            product_id=product.id,
            sku_ids=[sku_id]
        )
    
    def test_delete_already_deleted_returns_400(self, client, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=str(uuid4()),
            seller_id=str(seller_id),
            category_id=str(uuid4()),
            title="Test Product",
            description="Test Description",
            status="MODERATED",
            deleted=True,
            images=[],
            slug="test-product"
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/products/{product.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "ALREADY_DELETED"
    
    def test_delete_others_product_returns_403(self, client, db_session, valid_jwt_with_fixed_id, valid_jwt):
        token, seller_id = valid_jwt_with_fixed_id
        other_token = valid_jwt
        
        product = Product(
            id=str(uuid4()),
            seller_id=str(seller_id),
            category_id=str(uuid4()),
            title="Someone's Product",
            description="Test",
            status="MODERATED",
            deleted=False,
            images=[],
            slug="someones-product"
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/products/{product.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403
    
    def test_deleted_product_not_in_seller_list(self, client, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=str(uuid4()),
            seller_id=str(seller_id),
            category_id=str(uuid4()),
            title="Deleted Product",
            description="Should not appear",
            status="MODERATED",
            deleted=True,
            images=[],
            slug="deleted-product"
        )
        db_session.add(product)
        db_session.commit()
        pass