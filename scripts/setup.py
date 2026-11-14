"""Gera configuração pessoal sem imprimir ou transmitir credenciais."""
import getpass
import os
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    raise SystemExit(".env já existe; nenhuma configuração foi alterada.")
email = input("Seu e-mail para acessar o painel: ").strip().lower()
if "@" not in email or any(c in email for c in "\r\n#='\""):
    raise SystemExit("Informe um e-mail válido.")
password = getpass.getpass("Senha do painel (mínimo 12 caracteres): ")
if len(password) < 12 or len(password) > 200 or password != getpass.getpass("Repita a senha: "):
    raise SystemExit("Senhas não conferem ou tamanho inválido.")
if any(c in password for c in "\r\n'"):
    raise SystemExit("Esta configuração não aceita aspas simples ou quebras de linha na senha.")
text = (root / ".env.example").read_text()
text = text.replace("OWNER_EMAIL=voce@example.com", f"OWNER_EMAIL='{email}'")
text = text.replace("OWNER_PASSWORD=", f"OWNER_PASSWORD='{password}'")
text = text.replace("POSTGRES_PASSWORD=", f"POSTGRES_PASSWORD={secrets.token_hex(24)}")
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as stream:
    stream.write(text)
print(".env criado com permissão 600. Configure seu bot e seu provedor de dados nesse arquivo.")
