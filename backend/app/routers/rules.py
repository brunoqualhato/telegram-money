from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from ..auth import current_owner
from ..crud import audit
from ..db import get_db
from ..models import AlertRule, Asset
from ..schemas import RuleInput, Toggle

router = APIRouter(tags=["rules"])


@router.get("/api/rules")
def rules(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(
        [
            {**rule.__dict__, "ticker": ticker}
            for rule, ticker in db.execute(
                select(AlertRule, Asset.ticker).join(Asset).order_by(AlertRule.id.desc())
            ).all()
        ]
    )


@router.post("/api/rules", status_code=201)
def add_rule(data: RuleInput, owner=Depends(current_owner), db=Depends(get_db)):
    if not db.get(Asset, data.asset_id):
        raise HTTPException(404, "Cadastre o ativo antes de criar a regra")
    rule = AlertRule(**data.model_dump())
    db.add(rule)
    audit(db, "rule.create", f"{data.asset_id}:{data.kind}")
    db.commit()
    return jsonable_encoder(rule)


@router.patch("/api/rules/{rule_id}")
def toggle_rule(rule_id: int, data: Toggle, owner=Depends(current_owner), db=Depends(get_db)):
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(404, "Regra não encontrada")
    rule.enabled = data.enabled
    audit(db, "rule.toggle", str(rule_id))
    db.commit()
    return {"ok": True}


@router.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(404, "Regra não encontrada")
    audit(db, "rule.delete", str(rule_id))
    db.delete(rule)
    db.commit()
    return {"ok": True}
