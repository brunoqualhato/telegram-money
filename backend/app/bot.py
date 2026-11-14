import asyncio
from datetime import timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import delete, select
from .auth import digest
from .config import settings
from .db import SessionLocal, utcnow
from .models import AlertRule, Asset, AuditLog, CorporateAction, Owner, TelegramLink, TreasuryRate
from .services.alerts import latest_quote
from .services.reports import build_report
from .services.settings import get_app_setting

dispatcher = Dispatcher()
MENU = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Carteira", callback_data="carteira"),
            InlineKeyboardButton(text="🔔 Alertas", callback_data="alertas"),
        ],
        [
            InlineKeyboardButton(text="💰 Proventos", callback_data="proventos"),
            InlineKeyboardButton(text="🏛 Tesouro", callback_data="tesouro"),
        ],
        [InlineKeyboardButton(text="📝 Resumo", callback_data="resumo")],
    ]
)


def link_account(token, chat_id, username):
    with SessionLocal() as db:
        # DELETE RETURNING consome o código atomicamente inclusive no SQLite.
        owner_id = db.scalar(
            delete(TelegramLink)
            .where(TelegramLink.token_hash == digest(token), TelegramLink.expires_at > utcnow())
            .returning(TelegramLink.owner_id)
        )
        if not owner_id:
            return False
        owner = db.get(Owner, owner_id)
        owner.chat_id, owner.telegram_name = str(chat_id), username
        db.add(AuditLog(action="telegram.link", detail="Conta pessoal vinculada por código temporário"))
        db.commit()
        return True


def command_response(chat_id, text):
    with SessionLocal() as db:
        owner = db.scalar(select(Owner).where(Owner.chat_id == str(chat_id)))
        if not owner:
            return "Este chat não está vinculado. Abra Configurações no painel e gere um link de conexão."
        parts = text.strip().split()
        command = parts[0].split("@")[0].lower().lstrip("/") if parts else "ajuda"
        if command in ("carteira", "resumo", "atualizacao"):
            return build_report(db)
        if command == "cotacao":
            if len(parts) != 2:
                return "Use /cotacao PETR4. Cadastre o ativo no painel primeiro."
            asset = db.scalar(select(Asset).where(Asset.ticker == parts[1].upper()))
            quote = latest_quote(db, asset.id) if asset else None
            if not quote:
                return "Ativo não acompanhado ou ainda sem cotação. Confira o painel e o status da fonte de dados."
            delayed = utcnow() - quote.quoted_at.replace(tzinfo=utcnow().tzinfo) > timedelta(minutes=15)
            return (
                f"📈 {asset.ticker}\nCotação: {quote.currency} {quote.price:.2f}\nVariação: {quote.change_pct:+.2f}%\n"
                f"Horário da fonte: {quote.quoted_at.isoformat()}\nFonte: {quote.source}"
                + ("\n⚠ Cotação atrasada" if delayed else "")
            )
        if command == "proventos":
            rows = db.scalars(
                select(CorporateAction)
                .where(
                    CorporateAction.status == "confirmed", CorporateAction.ticker.in_(select(Asset.ticker))
                )
                .order_by(CorporateAction.payment_date.desc())
                .limit(12)
            ).all()
            return "💰 Proventos\n" + (
                "\n".join(f"{r.ticker} · {r.kind} · {r.amount} · pagamento {r.payment_date}" for r in rows)
                or "Nenhum evento coletado."
            )
        if command == "tesouro":
            rows = db.scalars(
                select(TreasuryRate).order_by(TreasuryRate.observed_on.desc(), TreasuryRate.title).limit(15)
            ).all()
            return "🏛 Tesouro Direto · taxas diárias, não tempo real\n" + (
                "\n".join(f"{r.title}: {r.rate:.2f}% · {r.observed_on}" for r in rows)
                or "Taxas ainda não coletadas."
            )
        if command == "alertas":
            rows = db.execute(
                select(AlertRule, Asset.ticker).join(Asset).where(AlertRule.enabled.is_(True))
            ).all()
            return "🔔 Alertas ativos\n" + (
                "\n".join(f"{ticker}: {r.kind} · {r.threshold:g}" for r, ticker in rows)
                or "Configure sua primeira regra no painel."
            )
        if command in ("pausar", "retomar", "sair"):
            if command == "sair":
                owner.chat_id, owner.telegram_name = None, None
            else:
                owner.notifications_enabled = command == "retomar"
            db.add(AuditLog(action=f"telegram.{command}", detail="Comando do proprietário"))
            db.commit()
            return {
                "pausar": "Alertas pausados. Use /retomar para reativar.",
                "retomar": "Alertas reativados.",
                "sair": "Telegram desvinculado. Seus ativos continuam salvos no painel.",
            }[command]
        return "Comandos: /carteira · /cotacao PETR4 · /proventos · /tesouro · /resumo · /alertas · /pausar · /retomar · /sair"


@dispatcher.message(CommandStart())
async def start(message: Message):
    if message.chat.type != "private":
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2:
        linked = await asyncio.to_thread(
            link_account, parts[1], message.chat.id, message.from_user.username if message.from_user else None
        )
        await message.answer(
            "✅ Telegram conectado. Configure seus alertas no painel."
            if linked
            else "Código inválido ou expirado. Gere outro link no painel.",
            reply_markup=MENU if linked else None,
        )
    else:
        await message.answer(await asyncio.to_thread(command_response, message.chat.id, "/ajuda"))


@dispatcher.callback_query(F.data.in_({"carteira", "alertas", "proventos", "tesouro", "resumo"}))
async def callback(query: CallbackQuery):
    await query.answer()
    if query.message and query.message.chat.type == "private":
        text = await asyncio.to_thread(command_response, query.message.chat.id, f"/{query.data}")
        await query.message.answer(text[:4000], reply_markup=MENU)


@dispatcher.message(F.text)
async def commands(message: Message):
    if message.chat.type != "private":
        return
    text = await asyncio.to_thread(command_response, message.chat.id, message.text)
    await message.answer(text[:4000], reply_markup=MENU)


async def main():
    with SessionLocal() as db:
        token = get_app_setting("telegram_bot_token", settings().telegram_bot_token, db=db)
    if not token or settings().demo_mode:
        raise SystemExit("Configure o token do Telegram no painel e desative DEMO_MODE para iniciar o bot.")
    bot = Bot(token)
    # Long polling não precisa de URL pública; não removemos webhooks existentes silenciosamente.
    info = await bot.get_webhook_info()
    if info.url:
        await bot.session.close()
        raise SystemExit(
            "Este bot tem webhook ativo. Use um bot dedicado ou remova o webhook conscientemente."
        )
    await dispatcher.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
