# src/services/event_service.py
import httpx
import structlog
from src.config import settings

logger = structlog.get_logger(__name__)


def send_edited_event(product_id: UUID, seller_id: UUID, changes: dict):
    """
    Отправка события EDITED в Moderation Service (синхронно)
    """
    import asyncio
    try:
        # Для синхронной отправки
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
        # В реальном проекте добавить retry