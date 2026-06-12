from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
from src.models.product import Product
from src.models.reserve_operation import ReserveOperation
from src.schemas.reserve import ReserveRequest, UnreserveRequest


class ReserveService:
    def __init__(self, db: Session):
        self.db = db

    def reserve(self, request: ReserveRequest) -> dict:
        existing = self.db.query(ReserveOperation).filter(
            ReserveOperation.idempotency_key == request.idempotency_key
        ).first()

        if existing:
            return existing.result

        sku_ids = [item.sku_id for item in request.items]

        products = self.db.query(Product).filter(
            Product.deleted == False
        ).all()

        sku_map = {}
        for product in products:
            for sku in (product.skus or []):
                if sku.get("id") in sku_ids:
                    sku_map[sku["id"]] = (product, sku)

        missing = set(sku_ids) - set(sku_map.keys())
        if missing:
            return {
                "reserved": False,
                "failed_items": [{
                    "sku_id": sid,
                    "requested": 0,
                    "available": 0,
                    "reason": "SKU_NOT_FOUND"
                } for sid in missing]
            }

        failed_items = []
        for item in request.items:
            product, sku = sku_map[item.sku_id]
            active = sku.get("active_quantity", 0)
            if active < item.quantity:
                failed_items.append({
                    "sku_id": item.sku_id,
                    "requested": item.quantity,
                    "available": active,
                    "reason": "OUT_OF_STOCK" if active == 0 else "INSUFFICIENT_STOCK"
                })

        if failed_items:
            return {
                "reserved": False,
                "failed_items": failed_items
            }

        result_items = []
        for item in request.items:
            product, sku = sku_map[item.sku_id]
            sku["active_quantity"] = sku.get("active_quantity", 0) - item.quantity
            sku["reserved_quantity"] = sku.get("reserved_quantity", 0) + item.quantity
            flag_modified(product, "skus")

            result_items.append({
                "sku_id": item.sku_id,
                "reserved_quantity": item.quantity,
                "remaining_stock": sku["active_quantity"]
            })

            if sku["active_quantity"] == 0:
                self._emit_out_of_stock_event(sku)

        response_data = {
            "reserved": True,
            "items": result_items
        }

        op = ReserveOperation(
            idempotency_key=request.idempotency_key,
            result=response_data
        )
        self.db.add(op)
        self.db.commit()

        return response_data

    def unreserve(self, request: UnreserveRequest) -> dict:
        sku_ids = [item.sku_id for item in request.items]

        products = self.db.query(Product).filter(
            Product.deleted == False
        ).all()

        sku_map = {}
        for product in products:
            for sku in (product.skus or []):
                if sku.get("id") in sku_ids:
                    sku_map[sku["id"]] = (product, sku)

        for item in request.items:
            if item.sku_id not in sku_map:
                return {
                    "code": "SKU_NOT_FOUND",
                    "message": f"SKU {item.sku_id} not found"
                }
            _, sku = sku_map[item.sku_id]
            if sku.get("reserved_quantity", 0) < item.quantity:
                return {
                    "code": "INSUFFICIENT_RESERVATION",
                    "message": f"Cannot unreserve {item.quantity}, only {sku.get('reserved_quantity', 0)} reserved"
                }

        for item in request.items:
            product, sku = sku_map[item.sku_id]
            sku["active_quantity"] = sku.get("active_quantity", 0) + item.quantity
            sku["reserved_quantity"] = sku.get("reserved_quantity", 0) - item.quantity
            flag_modified(product, "skus")

        self.db.commit()
        return {"ok": True}

    def _emit_out_of_stock_event(self, sku):
        from src.services.event_service import send_event_to_b2c
        send_event_to_b2c(
            event_type="SKU_OUT_OF_STOCK",
            payload={
                "sku_id": sku.get("id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
