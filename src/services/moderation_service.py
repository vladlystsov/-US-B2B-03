from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from src.models.product import Product
from src.models.processed_event import ProcessedEvent
from src.schemas.moderation import ModerationEventRequest


def apply_moderation_decision(
    db: Session,
    payload: ModerationEventRequest,
    sender_service: str = "moderation"
) -> dict:
    existing_event = db.query(ProcessedEvent).filter(
        ProcessedEvent.idempotency_key == payload.idempotency_key,
        ProcessedEvent.sender_service == sender_service
    ).first()

    if existing_event:
        return {"status": "duplicate", "idempotency_key": payload.idempotency_key}

    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise ValueError(f"Product {payload.product_id} not found")

    if payload.status == "MODERATED":
        product.status = Product.Status.MODERATED
        product.blocked = False
        product.blocking_reason_id = ""
        product.moderator_comment = ""
    elif payload.status == "BLOCKED":
        if payload.hard_block:
            product.status = Product.Status.HARD_BLOCKED
        else:
            product.status = Product.Status.BLOCKED
        product.blocked = True
        if payload.blocking_reason:
            product.blocking_reason_id = payload.blocking_reason.id
            product.moderator_comment = payload.blocking_reason.comment

        from src.services.event_service import send_event_to_b2c
        send_event_to_b2c(
            event_type="PRODUCT_BLOCKED",
            payload={
                "product_id": str(product.id),
                "hard_block": payload.hard_block
            }
        )

    db.add(ProcessedEvent(
        idempotency_key=payload.idempotency_key,
        sender_service=sender_service,
        event_type=payload.status
    ))

    db.commit()
    db.refresh(product)

    return {
        "status": "success",
        "product_id": product.id,
        "new_status": product.status
    }
