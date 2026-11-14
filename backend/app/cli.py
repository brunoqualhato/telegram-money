import argparse
import getpass
from pathlib import Path
from sqlalchemy import delete, select
from .auth import hash_password
from .db import SessionLocal
from .models import Asset, AuditLog, AuthSession, Owner
from .services.portfolio import parse_b3_position


def main():
    parser = argparse.ArgumentParser(description="Administração local do proprietário")
    parser.add_argument("command", choices=["reset-password", "import-b3"])
    parser.add_argument("file_path", nargs="?", help="Caminho do arquivo XLSX da B3 para importação")
    args = parser.parse_args()
    if args.command == "reset-password":
        password = getpass.getpass("Nova senha (12+ caracteres): ")
        if len(password) < 12 or password != getpass.getpass("Repita a senha: "):
            raise SystemExit("Senhas não conferem ou têm menos de 12 caracteres")
        with SessionLocal() as db:
            owner = db.scalar(select(Owner))
            if not owner:
                raise SystemExit("Configure OWNER_EMAIL e OWNER_PASSWORD e inicie a API primeiro")
            owner.password_hash = hash_password(password)
            db.execute(delete(AuthSession))
            db.add(
                AuditLog(
                    action="auth.password_reset",
                    detail="Senha alterada pelo terminal; todas as sessões revogadas",
                )
            )
            db.commit()
        print("Senha atualizada e sessões encerradas.")
    elif args.command == "import-b3":
        if not args.file_path:
            raise SystemExit("Informe o caminho do arquivo: python -m app.cli import-b3 <caminho.xlsx>")
        p = Path(args.file_path)
        if not p.is_file():
            raise SystemExit(f"Arquivo não encontrado: {p}")
        raw = p.read_bytes()
        items = parse_b3_position(raw, p.name)
        if not items:
            raise SystemExit("Nenhum ativo encontrado no arquivo.")
        with SessionLocal() as db:
            existing = {a.ticker: a for a in db.scalars(select(Asset)).all()}
            created = updated = 0
            for it in items:
                ticker = it["ticker"]
                if ticker in existing:
                    asset = existing[ticker]
                    asset.quantity = it["quantity"]
                    if it["name"] and not asset.name:
                        asset.name = it["name"]
                    if asset.average_price == 0:
                        asset.average_price = it["average_price"]
                    updated += 1
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
                    created += 1
            db.commit()
            print(f"Sucesso: {created} novos ativos criados, {updated} atualizados.")


if __name__ == "__main__":
    main()
