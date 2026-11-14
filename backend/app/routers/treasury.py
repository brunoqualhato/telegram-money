from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from ..auth import current_owner
from ..db import get_db
from ..models import TreasuryRate

router = APIRouter(tags=["treasury"])


@router.get("/api/treasury")
def treasury(owner=Depends(current_owner), db=Depends(get_db)):
    latest = db.scalar(select(func.max(TreasuryRate.observed_on)))
    return jsonable_encoder(
        db.scalars(
            select(TreasuryRate).where(TreasuryRate.observed_on == latest).order_by(TreasuryRate.title)
        ).all()
    )
