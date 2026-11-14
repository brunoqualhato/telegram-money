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
from ..schemas import AITestInput, SystemSettingsInput, TelegramTestInput
from ..services.ai import available_models
from ..services.alerts import enqueue
from ..services.settings import (
    get_all_settings,
    get_app_setting,
    save_settings,
    test_ai_endpoint_live,
    test_telegram_token_live,
    validate_ai_url,
)

router = APIRouter(tags=["integrations"])


@router.post("/api/telegram/link")
def telegram_link(owner=Depends(current_owner), db=Depends(get_db)):
    bot_token = get_app_setting("telegram_bot_token", db=db)
    bot_username = get_app_setting("telegram_bot_username", db=db)
    if not bot_token or not bot_username:
        raise HTTPException(
            503, "Configure o Token e Username do Bot do Telegram nas configurações para gerar o link."
        )
    if settings().demo_mode:
        raise HTTPException(409, "Modo demonstração não vincula contas reais")
    db.execute(delete(TelegramLink).where(TelegramLink.owner_id == owner.id))
    token = secrets.token_urlsafe(24)
    db.add(
        TelegramLink(token_hash=digest(token), owner_id=owner.id, expires_at=utcnow() + timedelta(minutes=15))
    )
    db.commit()
    username = bot_username.lstrip("@")
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

        poll_market.apply_async(kwargs={"force": True}, expires=120, retry=False)
        return {"message": "Coleta agendada. O painel atualizará automaticamente."}
    except Exception:
        from ..services.providers import collect_quotes

        count = collect_quotes(db)
        return {"message": f"Coleta de cotações concluída: {count} atualizações registradas."}


@router.get("/api/integrations")
def integrations(owner=Depends(current_owner), db=Depends(get_db)):
    all_cfg = get_all_settings(db)
    ai_prov = all_cfg.get("ai_provider", "lmstudio")
    ai_mod = all_cfg.get("lm_studio_model") if ai_prov == "lmstudio" else all_cfg.get("ollama_model")
    return {
        "telegram_configured": bool(all_cfg.get("telegram_bot_token") and all_cfg.get("telegram_bot_username")),
        "telegram_has_token": bool(all_cfg.get("telegram_bot_token")),
        "telegram_bot_username": all_cfg.get("telegram_bot_username", ""),
        "brapi_configured": bool(all_cfg.get("brapi_token")),
        "brapi_has_token": bool(all_cfg.get("brapi_token")),
        "ai_configured": bool(ai_mod),
        "ai_provider": ai_prov,
        "ai_model": ai_mod or "",
        "lm_studio_base_url": all_cfg.get("lm_studio_base_url", ""),
        "lm_studio_model": all_cfg.get("lm_studio_model", ""),
        "lm_studio_has_api_key": bool(all_cfg.get("lm_studio_api_key")),
        "ai_timeout_seconds": int(all_cfg.get("ai_timeout_seconds") or 180),
        "ollama_url": all_cfg.get("ollama_url", ""),
        "ollama_model": all_cfg.get("ollama_model", ""),
        "poll_seconds": int(all_cfg.get("poll_seconds") or 120),
        "demo": settings().demo_mode,
        "sources": jsonable_encoder(db.scalars(select(ProviderState).order_by(ProviderState.name)).all()),
        "capabilities": {
            "quotes": "Consulta aberta B3 (Status Invest / brapi) · Ações, FIIs, ETFs e BDRs sem necessidade de plano pago",
            "dividends": "Consulta aberta B3 · Dividendos, JCP e Rendimentos com datas com e pagamento",
            "treasury": "CSV oficial diário do Tesouro Nacional",
            "documents": "Importação de texto e PDF com resumo por IA local",
            "news": "Google News RSS financeiro automático para ativos acompanhados",
            "crypto_fx": "Cadastro permitido; coletores de cripto, câmbio e exterior ainda não implementados",
            "ai": f"{'LM Studio' if ai_prov == 'lmstudio' else 'Ollama'} · resumos com trechos verificáveis; não garante exatidão semântica",
        },
    }


@router.put("/api/integrations/settings")
def update_settings(data: SystemSettingsInput, owner=Depends(current_owner), db=Depends(get_db)):
    secrets = {"telegram_bot_token", "brapi_token", "lm_studio_api_key"}
    settings_dict = {
        key: str(value) for key, value in data.model_dump(exclude_unset=True).items()
        if key not in secrets or value
    }
    if "telegram_bot_username" in settings_dict:
        settings_dict["telegram_bot_username"] = settings_dict["telegram_bot_username"].lstrip("@")
    try:
        for key, provider in (("lm_studio_base_url", "lmstudio"), ("ollama_url", "ollama")):
            if key in settings_dict:
                settings_dict[key] = validate_ai_url(provider, settings_dict[key])
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    save_settings(db, settings_dict)
    audit(db, "system.update_settings", "Configurações de integração atualizadas pelo painel")
    db.commit()
    return {"ok": True, "message": "Configurações salvas com sucesso."}


@router.post("/api/integrations/test-telegram")
def test_telegram_integration(payload: TelegramTestInput, owner=Depends(current_owner)):
    return test_telegram_token_live(payload.token)


@router.post("/api/integrations/test-ai")
def test_ai_integration(payload: AITestInput, owner=Depends(current_owner)):
    return test_ai_endpoint_live(payload.provider, payload.url, payload.api_key)


@router.post("/api/ai/check")
def check_ai(owner=Depends(current_owner), db=Depends(get_db)):
    import httpx
    from ..services.providers import state

    try:
        from .. import main

        get_models = getattr(main, "available_models", available_models)
        try:
            models = get_models(db=db)
        except TypeError:
            models = get_models()
        cfg = get_all_settings(db)
        ai_prov = cfg.get("ai_provider", "lmstudio")
        selected = cfg.get("lm_studio_model") if ai_prov == "lmstudio" else cfg.get("ollama_model")
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
            "provider": ai_prov,
            "models": models,
            "configured_model": selected,
            "model_available": ready,
            "message": "Gateway acessível; modelo encontrado na lista. Isso não confirma carregamento ou geração; valide ao resumir um documento."
            if ready
            else "Gateway acessível. Configure o modelo desejado no menu de configurações.",
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
            "Gateway de IA indisponível. Confira a URL e o servidor de IA. Nenhum documento foi enviado neste teste.",
        )
