from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from ..auth import current_owner
from ..crud import audit, rows
from ..db import get_db
from ..models import CorporateAction
from ..schemas import EventInput
from ..services.events import upsert_event

router = APIRouter(tags=["events"])


@router.get("/api/events")
def events(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(rows(db, CorporateAction, 150))


@router.post("/api/events", status_code=201)
def import_event(data: EventInput, owner=Depends(current_owner), db=Depends(get_db)):
    row, changed = upsert_event(db, data)
    audit(db, "event.import", data.source_id)
    db.commit()
    return {"id": row.id, "changed": changed, "revision": row.revision}


@router.post("/api/events/refresh")
def refresh_events(owner=Depends(current_owner), db=Depends(get_db)):
    from ..services.providers import collect_dividends

    count = collect_dividends(db)
    return {"message": f"Busca de proventos concluída: {count} atualizações registradas.", "count": count}
