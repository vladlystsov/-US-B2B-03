from src.config import settings
from src.services import event_service


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


def test_product_deleted_cascades_include_receiver_service_keys(monkeypatch):
    calls = []
    monkeypatch.setattr(event_service.httpx, "Client", lambda: _Client(calls))

    event_service.send_deleted_event("product-1", "seller-1")
    event_service.send_product_deleted_to_b2c("product-1", ["sku-1"])

    assert len(calls) == 2
    assert calls[0][1]["headers"] == {"X-Service-Key": settings.MODERATION_SERVICE_KEY}
    assert calls[1][1]["headers"] == {"X-Service-Key": settings.B2C_SERVICE_KEY}
    assert calls[1][1]["json"]["payload"]["sku_ids"] == ["sku-1"]
