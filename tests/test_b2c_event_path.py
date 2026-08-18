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


def test_sku_out_of_stock_event_uses_b2c_b2b_events_path(monkeypatch):
    calls = []
    monkeypatch.setattr(event_service.httpx, "Client", lambda: _Client(calls))

    event_service.send_event_to_b2c(
        "SKU_OUT_OF_STOCK",
        {"sku_id": "sku-1", "product_id": "product-1"},
    )

    assert len(calls) == 1
    url, request = calls[0]
    assert url.endswith("/api/v1/b2b/events")
    assert request["json"]["event_type"] == "SKU_OUT_OF_STOCK"
