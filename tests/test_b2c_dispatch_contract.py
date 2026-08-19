from datetime import datetime, timezone

from src.config import settings
from src.models.b2c_cascade_outbox import B2CCascadeOutbox
from src.services import b2c_dispatcher


class _Response:
    def raise_for_status(self):
        return None


class _Client:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response()


def test_moderation_cascade_uses_b2c_event_contract(db_session, monkeypatch):
    event = B2CCascadeOutbox(
        id="b2b-event-1",
        event_type="PRODUCT_BLOCKED",
        product_id="product-1",
        payload={
            "product_id": "product-1",
            "sku_ids": ["sku-1"],
            "hard_block": True,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        },
        status="pending",
    )
    db_session.add(event)
    db_session.commit()
    calls = []
    monkeypatch.setattr(b2c_dispatcher, "httpx", __import__("httpx"))
    monkeypatch.setattr(b2c_dispatcher.httpx, "Client", lambda: _Client(calls))

    b2c_dispatcher.B2CDispatcher(base_url="http://b2c").send_pending_events(db_session)

    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "http://b2c/api/v1/b2b/events"
    assert kwargs["headers"] == {"X-Service-Key": settings.B2B_TO_B2C_KEY}
    assert kwargs["json"]["event_type"] == "PRODUCT_BLOCKED"
    assert kwargs["json"]["idempotency_key"] == "b2b-event-1"
    assert kwargs["json"]["payload"]["sku_ids"] == ["sku-1"]
    db_session.refresh(event)
    assert event.status == "sent"
