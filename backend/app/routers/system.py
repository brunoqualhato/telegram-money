from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text
from ..auth import current_owner
from ..config import settings
from ..crud import rows
from ..db import get_db
from ..models import AuditLog, Owner

router = APIRouter(tags=["system"])


@router.get("/health")
def health(db=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "version": "0.1.0"}


@router.get("/api/setup")
def setup(db=Depends(get_db)):
    return {"configured": bool(db.scalar(select(Owner.id))), "demo": settings().demo_mode}


@router.get("/api/audit")
def audit_log(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(rows(db, AuditLog, 100))
