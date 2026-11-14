from datetime import timedelta
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from ..auth import current_owner
from ..config import settings
from ..crud import audit, rows
from ..db import get_db, utcnow
from ..models import AlertRule, Asset, Notification, ProviderState, Quote
from ..schemas import AssetInput
from ..services.portfolio import parse_b3_position, portfolio_history, portfolio_snapshot

router = APIRouter(tags=["portfolio"])


@router.get("/api/overview")
def overview(owner=Depends(current_owner), db=Depends(get_db)):
    snapshot = portfolio_snapshot(db)
    snapshot.update(
        {
            "active_rules": db.scalar(
                select(func.count()).select_from(AlertRule).where(AlertRule.enabled.is_(True))
            ),
            "notifications_today": db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.created_at >= utcnow() - timedelta(hours=24))
            ),
            "telegram_connected": bool(owner.chat_id),
            "demo": settings().demo_mode,
            "latest_notifications": rows(db, Notification, 5),
            "providers": db.scalars(select(ProviderState).order_by(ProviderState.name)).all(),
        }
    )
    return jsonable_encoder(snapshot)


@router.get("/api/assets")
def assets(owner=Depends(current_owner), db=Depends(get_db)):
    return portfolio_snapshot(db)["assets"]


@router.post("/api/assets", status_code=201)
def add_asset(data: AssetInput, owner=Depends(current_owner), db=Depends(get_db)):
    if db.scalar(select(func.count()).select_from(Asset)) >= 50:
        raise HTTPException(422, "Esta versão pessoal suporta até 50 ativos por ciclo de coleta")
    asset = Asset(**data.model_dump())
    db.add(asset)
    try:
        db.flush()
        audit(db, "asset.create", data.ticker)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Este ativo já está na sua lista")
    return jsonable_encoder(asset)


@router.post("/api/assets/import-b3")
def import_b3(
    file: UploadFile = File(...),
    update_existing: bool = Form(default=True),
    update_average_price: bool = Form(default=False),
    owner=Depends(current_owner),
    db=Depends(get_db),
):
    raw = file.file.read(10_000_001)
    if len(raw) > 10_000_000:
        raise HTTPException(413, "Limite de 10 MB por arquivo")
    try:
        items = parse_b3_position(raw, file.filename or "")
    except Exception as e:
        raise HTTPException(422, f"Erro ao ler arquivo: {e}")
    if not items:
        raise HTTPException(
            422,
            "Nenhuma posição de Ação, FII, ETF ou BDR encontrada. Certifique-se de enviar a planilha de posição da Área do Investidor B3 (.xlsx ou .csv).",
        )
    existing = {a.ticker: a for a in db.scalars(select(Asset)).all()}
    items = [item for item in items if item["quantity"] > 0 or item["ticker"] in existing]
    new_items = [it for it in items if it["ticker"] not in existing]
    if len(existing) + len(new_items) > 50:
        raise HTTPException(
            422,
            f"Esta versão pessoal suporta até 50 ativos. A carteira já possui {len(existing)} ativos e o arquivo contém {len(new_items)} novos (total: {len(existing) + len(new_items)}).",
        )
    created_count = 0
    updated_count = 0
    for it in items:
        ticker = it["ticker"]
        if ticker in existing:
            if update_existing:
                asset = existing[ticker]
                asset.quantity = it["quantity"]
                if it["name"] and not asset.name:
                    asset.name = it["name"]
                if it.get("average_price_known", True) and (update_average_price or asset.average_price == 0):
                    asset.average_price = it["average_price"]
                updated_count += 1
        else:
            asset = Asset(
                ticker=ticker,
                name=it["name"],
                asset_class=it["asset_class"],
                watchlist="Principal",
                quantity=it["quantity"],
                average_price=it["average_price"],
            )
            db.add(asset)
            created_count += 1
    audit(
        db,
        "asset.import_b3",
        f"Importação B3: {created_count} criados, {updated_count} atualizados a partir de {file.filename or 'arquivo'}",
    )
    db.commit()
    return {
        "imported": created_count,
        "updated": updated_count,
        "total": created_count + updated_count,
        "message": f"Importação da B3 concluída: {created_count} novos ativos adicionados e {updated_count} atualizados.",
    }


@router.put("/api/assets/{asset_id}")
def update_asset(asset_id: int, data: AssetInput, owner=Depends(current_owner), db=Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "Ativo não encontrado")
    if data.ticker != asset.ticker:
        raise HTTPException(
            422, "Remova e cadastre outro ativo para trocar o ticker; o histórico pertence ao ticker original"
        )
    for key, value in data.model_dump().items():
        setattr(asset, key, value)
    audit(db, "asset.update", asset.ticker)
    db.commit()
    return {"ok": True}


@router.delete("/api/assets/{asset_id}")
def delete_asset(asset_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "Ativo não encontrado")
    audit(db, "asset.delete", asset.ticker)
    db.delete(asset)
    db.commit()
    return {"ok": True}


@router.get("/api/assets/{asset_id}/history")
def quote_history(asset_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(
        db.scalars(
            select(Quote).where(Quote.asset_id == asset_id).order_by(Quote.quoted_at.desc()).limit(120)
        ).all()
    )


@router.get("/api/portfolio/history")
def get_portfolio_history(days: int = Query(30, ge=1, le=400), owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(portfolio_history(db, days=days))
