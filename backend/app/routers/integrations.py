from datetime import timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select
from ..auth import current_owner, digest
from ..config import settings
from ..crud import audit
from ..db import get_db, utcnow
from ..models import ProviderState, TelegramLink
from ..services.ai import available_models
from ..services.alerts import enqueue

router = APIRouter(tags=["integrations"])


@router.post("/api/telegram/link")
def telegram_link(owner=Depends(current_owner), db=Depends(get_db)):
    if not settings().telegram_bot_token or not settings().telegram_bot_username:
        raise HTTPException(
            503, "Configure TELEGRAM_BOT_TOKEN e TELEGRAM_BOT_USERNAME no .env e reinicie os serviços"
        )
    if settings().demo_mode:
        raise HTTPException(409, "Modo demonstração não vincula contas reais")
    db.execute(delete(TelegramLink).where(TelegramLink.owner_id == owner.id))
    token = secrets.token_urlsafe(24)
    db.add(
        TelegramLink(token_hash=digest(token), owner_id=owner.id, expires_at=utcnow() + timedelta(minutes=15))
    )
    db.commit()
    username = settings().telegram_bot_username.lstrip("@")
    return {"url": f"https://t.me/{username}?start={token}", "expires_in": 900}


@router.delete("/api/telegram/link")
def unlink_telegram(owner=Depends(current_owner), db=Depends(get_db)):
    owner.chat_id, owner.telegram_name = None, None
    db.execute(delete(TelegramLink).where(TelegramLink.owner_id == owner.id))
    audit(db, "telegram.unlink", "Telegram desvinculado pelo painel")
    db.commit()
    return {"ok": True}


@router.post("/api/telegram/test")
def test_telegram(owner=Depends(current_owner), db=Depends(get_db)):
    if not owner.chat_id:
        raise HTTPException(409, "Conecte seu Telegram primeiro")
    enqueue(
        db,
        f"test:{secrets.token_hex(12)}",
        "test",
        "Teste de conexão",
        "✅ Telegram Money conectado. Esta é uma mensagem de teste solicitada pelo painel.",
    )
    db.commit()
    return {"message": "Teste colocado na fila; respeita pausa, silêncio e limite de frequência"}


@router.post("/api/market/refresh")
def refresh_market(owner=Depends(current_owner), db=Depends(get_db)):
    if settings().demo_mode:
        raise HTTPException(
            409, "Demonstração usa exemplos fixos; desative DEMO_MODE para coletar dados reais"
        )
    try:
        from ..tasks import poll_market

        poll_market.apply_async(expires=120, retry=False)
        return {"message": "Coleta agendada. O painel atualizará automaticamente."}
    except Exception:
        from ..services.providers import collect_quotes

        count = collect_quotes(db)
        return {"message": f"Coleta de cotações concluída: {count} atualizações registradas."}


@router.get("/api/integrations")
def integrations(owner=Depends(current_owner), db=Depends(get_db)):
    return {
        "telegram_configured": bool(settings().telegram_bot_token and settings().telegram_bot_username),
        "brapi_configured": bool(settings().brapi_token),
        "ai_configured": bool(settings().ai_model),
        "ai_provider": settings().ai_provider,
        "ai_model": settings().ai_model,
        "poll_seconds": settings().poll_seconds,
        "demo": settings().demo_mode,
        "sources": jsonable_encoder(db.scalars(select(ProviderState).order_by(ProviderState.name)).all()),
        "capabilities": {
            "quotes": "Consulta aberta B3 (Status Invest / brapi) · Ações, FIIs, ETFs e BDRs sem necessidade de plano pago",
            "dividends": "Consulta aberta B3 · Dividendos, JCP e Rendimentos com datas com e pagamento",
            "treasury": "CSV oficial diário do Tesouro Nacional",
            "documents": "Importação de texto e PDF com resumo por IA local",
            "news": "Google News RSS financeiro automático para ativos acompanhados",
            "crypto_fx": "Cadastro permitido; coletores de cripto, câmbio e exterior ainda não implementados",
            "ai": f"{'LM Studio' if settings().ai_provider == 'lmstudio' else 'Ollama'} · resumos com trechos verificáveis; não garante exatidão semântica",
        },
    }


@router.post("/api/ai/check")
def check_ai(owner=Depends(current_owner), db=Depends(get_db)):
    import httpx
    from ..services.providers import state

    try:
        from .. import main

        get_models = getattr(main, "available_models", available_models)
        models = get_models()
        selected = settings().ai_model
        ready = bool(selected and selected in models)
        state(
            db,
            "ai",
            None
            if ready
            else "Gateway acessível, mas o modelo configurado não aparece na lista de modelos disponíveis.",
        )
        db.commit()
        return {
            "provider": settings().ai_provider,
            "models": models,
            "configured_model": selected,
            "model_available": ready,
            "message": "Gateway acessível; modelo encontrado na lista. Isso não confirma carregamento ou geração; valide ao resumir um documento."
            if ready
            else "Gateway acessível. Configure o ID exato de um dos modelos listados no .env e reinicie os serviços.",
        }
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        state(
            db,
            "ai",
            "Não foi possível consultar o gateway. Confira URL, servidor ativo e token de autenticação.",
        )
        db.commit()
        raise HTTPException(
            503,
            "Gateway de IA indisponível. Confira a URL, o servidor LM Studio/Ollama e o token. Nenhum documento foi enviado neste teste.",
        )
