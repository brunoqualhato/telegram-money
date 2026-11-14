import secrets
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from ..auth import current_owner
from ..crud import rows
from ..db import get_db
from ..models import MarketReport
from ..services.reports import create_report

router = APIRouter(tags=["reports"])


@router.get("/api/reports")
def reports(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(rows(db, MarketReport, 60))


@router.post("/api/reports")
def report(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(create_report(db, "demand", f"demand:{secrets.token_hex(12)}"))
