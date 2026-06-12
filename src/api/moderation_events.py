from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.config import settings
from src.schemas.moderation import ModerationEventRequest
from src.services.moderation_service import apply_moderation_decision

router = APIRouter(prefix="/api/v1/events", tags=["Moderation Events"])


def verify_service_key(x_service_key: Optional[str] = Header(None)):
    if not x_service_key or x_service_key != settings.MODERATION_SERVICE_KEY:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or missing X-Service-Key"}
        )
    return True


@router.post("/moderation")
def handle_moderation_event(
    payload: ModerationEventRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_service_key)
):
    try:
        result = apply_moderation_decision(db, payload)
        return {"ok": True, "status": result["status"]}
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": str(e)})
    except Exception:
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "Internal server error"})
