import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import patch

from src.main import app
from src.models.product import Product

client = TestClient(app)


class TestProductEdit:
    
    @pytest.fixture
    def created_product(self, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        response = client.post(
            "/api/v1/products",
            json={
                "title": "Test Product",
                "description": "Test Description",
                "category_id": str(uuid4()),
                "images": [{"url": "/s3/test.jpg", "ordering": 0}]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        return response.json()["id"], token, seller_id
    
    def test_edit_moderated_product_returns_to_on_moderation(self, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
    
        product = Product(
            id=uuid4(),
            seller_id=seller_id,
            category_id=uuid4(),
            title="Original Title",
            description="Original Description",
            status=Product.Status.MODERATED,
            images=[],
            slug="original-slug"
        )
        db_session.add(product)
        db_session.commit()
        
        with patch('src.services.event_service.send_edited_event') as mock_event:
            response = client.put(
                f"/api/v1/products/{product.id}",
                json={
                    "title": "Updated Title",
                    "description": "Updated Description"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        db_session.refresh(product)
        assert product.status == Product.Status.ON_MODERATION
        assert product.title == "Updated Title"
        mock_event.assert_called_once()
    
    def test_edit_blocked_product_returns_to_on_moderation(self, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=uuid4(),
            seller_id=seller_id,
            category_id=uuid4(),
            title="Blocked Product",
            description="Bad description",
            status=Product.Status.BLOCKED,
            blocked=True,
            moderator_comment="Bad photo quality",
            images=[],
            slug="blocked-product"
        )
        db_session.add(product)
        db_session.commit()
        
        with patch('src.services.event_service.send_edited_event') as mock_event:
            response = client.put(
                f"/api/v1/products/{product.id}",
                json={
                    "title": "Fixed Title",
                    "description": "Fixed description with good photo"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        db_session.refresh(product)
        assert product.status == Product.Status.ON_MODERATION
        mock_event.assert_called_once()
    
    def test_edit_hard_blocked_returns_403(self, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=uuid4(),
            seller_id=seller_id,
            category_id=uuid4(),
            title="Hard Blocked Product",
            description="Violation of terms",
            status=Product.Status.HARD_BLOCKED,
            blocked=True,
            images=[],
            slug="hard-blocked"
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.put(
            f"/api/v1/products/{product.id}",
            json={"title": "Try to edit"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        error_detail = response.json().get("detail", "")
        assert "hard blocked" in error_detail.lower()
        
        db_session.refresh(product)
        assert product.status == Product.Status.HARD_BLOCKED
        assert product.title == "Hard Blocked Product"
    
    def test_edit_others_product_returns_403(self, db_session, valid_jwt_with_fixed_id, valid_jwt):
        token, seller_id = valid_jwt_with_fixed_id
        other_token = valid_jwt
        
        product = Product(
            id=uuid4(),
            seller_id=seller_id,
            category_id=uuid4(),
            title="Someone's Product",
            description="Original description",
            status=Product.Status.MODERATED,
            images=[],
            slug="someones-product"
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.put(
            f"/api/v1/products/{product.id}",
            json={"title": "Hijack Attempt"},
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403
        assert "not found" in response.json().get("detail", "").lower() or "access" in response.json().get("detail", "").lower()
        
        db_session.refresh(product)
        assert product.title == "Someone's Product"
    
    def test_edit_created_product_does_not_change_status(self, db_session, valid_jwt_with_fixed_id):
        token, seller_id = valid_jwt_with_fixed_id
        
        product = Product(
            id=uuid4(),
            seller_id=seller_id,
            category_id=uuid4(),
            title="Created Product",
            description="New product",
            status=Product.Status.CREATED,
            images=[],
            slug="created-product"
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.put(
            f"/api/v1/products/{product.id}",
            json={"description": "Updated description"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        db_session.refresh(product)
        assert product.status == Product.Status.CREATED