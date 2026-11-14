from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from ..auth import current_owner
from ..crud import audit, rows
from ..db import get_db, utcnow
from ..models import Notification

router = APIRouter(tags=["notifications"])


@router.get("/api/notifications")
def notifications(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(rows(db, Notification, 150))


@router.post("/api/notifications/{notification_id}/retry")
def retry_notification(notification_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    row = db.get(Notification, notification_id)
    if not row or row.status not in ("failed", "uncertain"):
        raise HTTPException(409, "Somente falhas e entregas incertas podem ser reenviadas")
    row.status, row.error, row.attempts, row.next_attempt = "pending", None, 0, utcnow()
    audit(db, "notification.retry", f"Reenvio manual da notificação {row.id}")
    db.commit()
    return {"ok": True}
