import httpx
import structlog
from uuid import UUID
from datetime import datetime
from src.config import settings

logger = structlog.get_logger(__name__)


def send_edited_event(product_id: UUID, seller_id: UUID, changes: dict):
    """
    Отправка события EDITED в Moderation Service (синхронно)
    """
    import asyncio
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{settings.MODERATION_SERVICE_URL}/api/v1/events",
                json={
                    "event_type": "EDITED",
                    "product_id": str(product_id),
                    "seller_id": str(seller_id),
                    "changes": changes
                },
                timeout=5.0
            )
            response.raise_for_status()
            logger.info("product_edited_event_sent", product_id=str(product_id))
    except Exception as e:
        logger.error("failed_to_send_edited_event", product_id=str(product_id), error=str(e))


def send_deleted_event(product_id: str, seller_id: str) -> None:
    """Событие DELETED → Moderation Service"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{settings.MODERATION_SERVICE_URL}/api/v1/events",
                json={
                    "event_type": "DELETED",
                    "product_id": product_id,
                    "seller_id": seller_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                timeout=5.0
            )
            response.raise_for_status()
            logger.info("product_deleted_event_sent", product_id=product_id)
    except Exception as e:
        logger.error("failed_to_send_deleted_event", product_id=product_id, error=str(e))


def send_product_deleted_to_b2c(product_id: str, sku_ids: list) -> None:
    """Событие PRODUCT_DELETED → B2C сервис (для очистки корзин)"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{settings.B2C_SERVICE_URL}/api/v1/events/product-deleted",
                json={
                    "product_id": product_id,
                    "sku_ids": sku_ids,
                    "timestamp": datetime.utcnow().isoformat()
                },
                timeout=5.0
            )
            response.raise_for_status()
            logger.info("product_deleted_b2c_event_sent", product_id=product_id, sku_count=len(sku_ids))
    except Exception as e:
        logger.error("failed_to_send_b2c_event", product_id=product_id, error=str(e))