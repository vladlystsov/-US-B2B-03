import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch

from src.models.product import Product
from src.config import settings


class TestModerationEvents:

    def test_moderated_event_clears_blocking_data(self, client, db_session):
        """MODERATED event: status=MODERATED, blocking data cleared"""
        product = Product(
            id=str(uuid4()),
            seller_id=str(uuid4()),
            category_id=str(uuid4()),
            title="Blocked Product",
            slug="blocked",
            description="Description",
            status=Product.Status.BLOCKED,
            deleted=False,
            blocked=True,
            blocking_reason_id=str(uuid4()),
            moderator_comment="Bad content",
            images=[],
            characteristics=[],
            skus=[]
        )
        db_session.add(product)
        db_session.commit()

        response = client.post(
            "/api/v1/events/moderation",
            json={
                "idempotency_key": str(uuid4()),
                "product_id": str(product.id),
                "status": "MODERATED"
            },
            headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY}
        )

        assert response.status_code == 200
        db_session.refresh(product)
        assert product.status == Product.Status.MODERATED
        assert product.blocked is False
        assert product.moderator_comment == ""

    def test_blocked_soft_saves_field_reports(self, client, db_session):
        """BLOCKED soft: status=BLOCKED, field_reports saved, B2C cascade"""
        product = Product(
            id=str(uuid4()),
            seller_id=str(uuid4()),
            category_id=str(uuid4()),
            title="Soft Block Test",
            slug="soft-block",
            description="Description",
            status=Product.Status.MODERATED,
            deleted=False,
            blocked=False,
            images=[],
            characteristics=[],
            skus=[]
        )
        db_session.add(product)
        db_session.commit()

        with patch('src.services.event_service.send_event_to_b2c') as mock_b2c:
            response = client.post(
                "/api/v1/events/moderation",
                json={
                    "idempotency_key": str(uuid4()),
                    "product_id": str(product.id),
                    "status": "BLOCKED",
                    "hard_block": False,
                    "blocking_reason": {
                        "id": str(uuid4()),
                        "title": "Bad photos",
                        "comment": "Blurry images"
                    },
                    "field_reports": [
                        {"field_name": "images", "comment": "Low quality"}
                    ]
                },
                headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY}
            )

        assert response.status_code == 200
        db_session.refresh(product)
        assert product.status == Product.Status.BLOCKED
        assert product.blocked is True
        mock_b2c.assert_called_once()

    def test_blocked_hard_sets_terminal_status(self, client, db_session):
        """BLOCKED hard: HARD_BLOCKED, B2C cascade"""
        product = Product(
            id=str(uuid4()),
            seller_id=str(uuid4()),
            category_id=str(uuid4()),
            title="Hard Block Test",
            slug="hard-block",
            description="Description",
            status=Product.Status.MODERATED,
            deleted=False,
            blocked=False,
            images=[],
            characteristics=[],
            skus=[]
        )
        db_session.add(product)
        db_session.commit()

        with patch('src.services.event_service.send_event_to_b2c') as mock_b2c:
            response = client.post(
                "/api/v1/events/moderation",
                json={
                    "idempotency_key": str(uuid4()),
                    "product_id": str(product.id),
                    "status": "BLOCKED",
                    "hard_block": True,
                    "blocking_reason": {
                        "id": str(uuid4()),
                        "title": "Fraud",
                        "comment": "Scam product"
                    }
                },
                headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY}
            )

        assert response.status_code == 200
        db_session.refresh(product)
        assert product.status == Product.Status.HARD_BLOCKED
        assert product.blocked is True
        mock_b2c.assert_called_once()

    def test_duplicate_event_same_idempotency_key_no_side_effects(self, client, db_session):
        """Duplicate event with same idempotency_key → no changes"""
        product = Product(
            id=str(uuid4()),
            seller_id=str(uuid4()),
            category_id=str(uuid4()),
            title="Duplicate Test",
            slug="duplicate",
            description="Description",
            status=Product.Status.MODERATED,
            deleted=False,
            blocked=False,
            images=[],
            characteristics=[],
            skus=[]
        )
        db_session.add(product)
        db_session.commit()

        idempotency_key = str(uuid4())

        response1 = client.post(
            "/api/v1/events/moderation",
            json={
                "idempotency_key": idempotency_key,
                "product_id": str(product.id),
                "status": "BLOCKED",
                "hard_block": True,
                "blocking_reason": {"id": str(uuid4()), "title": "Fraud", "comment": "Scam"}
            },
            headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY}
        )
        assert response1.status_code == 200

        response2 = client.post(
            "/api/v1/events/moderation",
            json={
                "idempotency_key": idempotency_key,
                "product_id": str(product.id),
                "status": "MODERATED"
            },
            headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY}
        )
        assert response2.status_code == 200
        assert response2.json()["status"] == "duplicate"

        db_session.refresh(product)
        assert product.status == Product.Status.HARD_BLOCKED

    def test_missing_service_key_returns_401(self, client, db_session):
        """No X-Service-Key → 401"""
        response = client.post(
            "/api/v1/events/moderation",
            json={
                "idempotency_key": str(uuid4()),
                "product_id": str(uuid4()),
                "status": "MODERATED"
            }
        )
        assert response.status_code == 401
