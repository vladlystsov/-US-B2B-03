import httpx
from sqlalchemy.orm import Session
from src.models.b2c_cascade_outbox import B2CCascadeOutbox
from src.config import settings


class B2CDispatcher:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, "B2C_SERVICE_URL", "http://localhost:8002")

    def send_pending_events(self, db: Session):
        events = db.query(B2CCascadeOutbox).filter(
            B2CCascadeOutbox.status == "pending"
        ).all()

        for event in events:
            try:
                with httpx.Client() as client:
                    response = client.post(
                        f"{self.base_url}/api/v1/b2b/events",
                        json={
                            "event_type": event.event_type,
                            "idempotency_key": event.id,
                            "occurred_at": event.payload["occurred_at"],
                            "payload": event.payload,
                        },
                        headers={"X-Service-Key": settings.B2B_TO_B2C_KEY},
                        timeout=5.0,
                    )
                    response.raise_for_status()
                event.status = "sent"
            except Exception:
                event.status = "failed"

        if events:
            db.commit()


b2c_dispatcher = B2CDispatcher()
