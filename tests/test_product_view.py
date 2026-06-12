# tests/test_product_view.py
import pytest
from uuid import uuid4
from src.models.product import Product
from src.models.blocking import BlockingReason, ProductBlocking

class TestProductView:
    
    def test_get_moderated_product_returns_full_payload(self, client, db_session, valid_jwt_with_fixed_id):
        """MODERATED: полные данные, blocking_reason=null"""
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=str(uuid4()),
            seller_id=seller_id,
            title="Test Product",
            status=Product.Status.MODERATED,
            deleted=False,
            blocked=False,
            skus=[{"id": "s1", "price": 10000, "cost_price": 7000, "reserved_quantity": 2}]
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/products/{product.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "MODERATED"
        assert data.get("blocking_reason") is None
        assert data["skus"][0]["cost_price"] == 7000
        assert data["skus"][0]["reserved_quantity"] == 2
    
    def test_get_blocked_product_returns_blocking_reason_and_field_reports(self, client, db_session, valid_jwt_with_fixed_id):
        """BLOCKED: blocking_reason + field_reports"""
        token, seller_id = valid_jwt_with_fixed_id
        
        reason = BlockingReason(
            id=str(uuid4()),
            title="Нарушение оферты",
            description="Товар нарушает правила"
        )
        db_session.add(reason)
        
        product = Product(
            id=str(uuid4()),
            seller_id=seller_id,
            title="Bad Product",
            status=Product.Status.BLOCKED,
            blocked=True,
            skus=[]
        )
        db_session.add(product)
        
        product_blocking = ProductBlocking(
            product_id=product.id,
            blocking_reason_id=reason.id,
            field_reports=[
                {"field": "title", "message": "Использование запрещённых слов"},
                {"field": "images", "message": "Изображение содержит логотип"}
            ]
        )
        db_session.add(product_blocking)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/products/{product.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "BLOCKED"
        assert data["blocking_reason"]["title"] == "Нарушение оферты"
        assert len(data["field_reports"]) == 2
        assert data["field_reports"][0]["field"] == "title"
    
    def test_get_others_product_returns_404(self, client, db_session, valid_jwt_with_fixed_id, valid_jwt):
        """Чужой товар → 404 (не 403)"""
        token, owner_id = valid_jwt_with_fixed_id
        other_token = valid_jwt
        
        product = Product(
            id=str(uuid4()),
            seller_id=owner_id,
            title="Someone's Product",
            status=Product.Status.MODERATED
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/products/{product.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 404
    
    def test_get_nonexistent_returns_404(self, client, valid_jwt_with_fixed_id):
        """Несуществующий ID → 404"""
        token, _ = valid_jwt_with_fixed_id
        fake_id = uuid4()
        
        response = client.get(
            f"/api/v1/products/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404