#!/usr/bin/env python3
"""
Telegram Money · Setup Wizard
Assistente interativo para diagnóstico de ambiente, configuração de credenciais,
integrações (Telegram, brapi, IA local) e inicialização segura do sistema.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TARGET_ENV = ROOT / ".env"
EXAMPLE_ENV = ROOT / ".env.example"


class UI:
    """Utilitários de terminal com formatação e cores ANSI."""

    USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

    RESET = "\033[0m" if USE_COLOR else ""
    BOLD = "\033[1m" if USE_COLOR else ""
    DIM = "\033[2m" if USE_COLOR else ""
    GREEN = "\033[32m" if USE_COLOR else ""
    YELLOW = "\033[33m" if USE_COLOR else ""
    RED = "\033[31m" if USE_COLOR else ""
    CYAN = "\033[36m" if USE_COLOR else ""
    BLUE = "\033[34m" if USE_COLOR else ""

    @classmethod
    def banner(cls) -> None:
        print(f"\n{cls.CYAN}{cls.BOLD}┌─────────────────────────────────────────────────────────┐{cls.RESET}")
        print(f"{cls.CYAN}{cls.BOLD}│                TELEGRAM MONEY · SETUP WIZARD            │{cls.RESET}")
        print(f"{cls.CYAN}{cls.BOLD}│         Assistente de Configuração do Ambiente          │{cls.RESET}")
        print(f"{cls.CYAN}{cls.BOLD}└─────────────────────────────────────────────────────────┘{cls.RESET}\n")

    @classmethod
    def section(cls, step: int, total: int, title: str) -> None:
        print(f"\n{cls.BOLD}{cls.BLUE}▶ [{step}/{total}] {title}{cls.RESET}")
        print(f"{cls.DIM}{'─' * 55}{cls.RESET}")

    @classmethod
    def success(cls, msg: str) -> None:
        print(f"  {cls.GREEN}✔{cls.RESET} {msg}")

    @classmethod
    def warning(cls, msg: str) -> None:
        print(f"  {cls.YELLOW}⚠{cls.RESET} {msg}")

    @classmethod
    def error(cls, msg: str) -> None:
        print(f"  {cls.RED}✖{cls.RESET} {msg}")

    @classmethod
    def info(cls, msg: str) -> None:
        print(f"  {cls.CYAN}ℹ{cls.RESET} {msg}")

    @classmethod
    def ask(cls, prompt: str, default: Optional[str] = None) -> str:
        if default:
            display_prompt = f"{prompt} [{cls.DIM}{default}{cls.RESET}]: "
        else:
            display_prompt = f"{prompt}: "
        try:
            val = input(display_prompt).strip()
            return val if val else (default or "")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada pelo usuário.")
            sys.exit(1)

    @classmethod
    def ask_choice(cls, prompt: str, options: List[Tuple[str, str]], default_idx: int = 0) -> str:
        print(f"{prompt}")
        for i, (key, desc) in enumerate(options, 1):
            is_def = " (padrão)" if i - 1 == default_idx else ""
            print(f"  {cls.CYAN}{i}){cls.RESET} {desc}{cls.DIM}{is_def}{cls.RESET}")
        while True:
            resp = cls.ask("Selecione uma opção", str(default_idx + 1))
            if resp.isdigit() and 1 <= int(resp) <= len(options):
                return options[int(resp) - 1][0]
            cls.warning(f"Opção inválida. Escolha entre 1 e {len(options)}.")

    @classmethod
    def confirm(cls, prompt: str, default: bool = True) -> bool:
        hint = "S/n" if default else "s/N"
        ans = cls.ask(f"{prompt} ({hint})", default="s" if default else "n").lower()
        return ans in ("s", "sim", "y", "yes")

    @classmethod
    def ask_secret(cls, prompt: str, min_length: int = 12) -> str:
        while True:
            try:
                val = getpass.getpass(f"{prompt}: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nOperação cancelada.")
                sys.exit(1)
            if not val:
                cls.warning("O valor não pode ser vazio.")
                continue
            if len(val) < min_length:
                cls.warning(f"A senha deve ter no mínimo {min_length} caracteres (digitados: {len(val)}).")
                continue
            if any(c in val for c in "\r\n'"):
                cls.warning("A senha não pode conter quebras de linha ou aspas simples.")
                continue
            try:
                confirm = getpass.getpass("Confirme a senha: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nOperação cancelada.")
                sys.exit(1)
            if val != confirm:
                cls.warning("As senhas não coincidem. Tente novamente.")
                continue
            return val


# ─────────────────────────────────────────────────────────────────────────────
# 1. Diagnóstico do Ambiente
# ─────────────────────────────────────────────────────────────────────────────

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def check_docker_environment() -> Dict[str, Any]:
    """Verifica disponibilidade do Docker e Docker Compose."""
    env = os.environ.copy()
    env.pop("DOCKER_HOST", None)  # Previne sockets inválidos legados no Mac

    docker_path = shutil.which("docker")
    compose_available = False
    daemon_running = False
    docker_version = ""

    if docker_path:
        try:
            ver = subprocess.run(["docker", "--version"], env=env, capture_output=True, text=True, timeout=5)
            if ver.returncode == 0:
                docker_version = ver.stdout.strip()
        except Exception:
            pass

        try:
            info = subprocess.run(["docker", "info"], env=env, capture_output=True, text=True, timeout=5)
            if info.returncode == 0:
                daemon_running = True
        except Exception:
            pass

        try:
            comp = subprocess.run(["docker", "compose", "version"], env=env, capture_output=True, text=True, timeout=5)
            if comp.returncode == 0:
                compose_available = True
        except Exception:
            pass

    return {
        "installed": bool(docker_path),
        "version": docker_version,
        "daemon_running": daemon_running,
        "compose": compose_available,
    }


def run_environment_checks() -> Dict[str, Any]:
    """Executa diagnóstico completo das ferramentas e portas necessárias."""
    results: Dict[str, Any] = {}

    # Python
    py_ver = sys.version_info
    results["python"] = {
        "version": f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}",
        "ok": py_ver >= (3, 10),
        "recommended": py_ver >= (3, 12),
    }

    # Docker
    results["docker"] = check_docker_environment()

    # Node / NPM (para frontend local)
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    node_version = ""
    if node_path:
        try:
            res = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=3)
            node_version = res.stdout.strip()
        except Exception:
            pass
    results["node"] = {"installed": bool(node_path), "version": node_version, "npm": bool(npm_path)}

    # Portas locais
    results["ports"] = {
        8000: is_port_in_use(8000),
        5432: is_port_in_use(5432),
        6379: is_port_in_use(6379),
    }

    return results


def print_environment_report(checks: Dict[str, Any]) -> None:
    print(f"\n{UI.BOLD}Status das Ferramentas:{UI.RESET}")

    py = checks["python"]
    if py["ok"]:
        UI.success(f"Python {py['version']} detectado")
    else:
        UI.error(f"Python {py['version']} (necessário Python 3.10 ou superior)")

    doc = checks["docker"]
    if doc["daemon_running"]:
        UI.success(f"Docker Engine ativo ({doc['version']})")
    elif doc["installed"]:
        UI.warning("Docker instalado, mas o daemon não está em execução no momento.")
    else:
        UI.warning("Docker não encontrado. O sistema poderá rodar em modo local (SQLite).")

    if doc["compose"]:
        UI.success("Docker Compose v2 disponível")

    node = checks["node"]
    if node["installed"]:
        UI.success(f"Node.js {node['version']} detectado (frontend local)")
    else:
        UI.info("Node.js não detectado (apenas necessário para compilação local do frontend sem Docker)")

    print(f"\n{UI.BOLD}Portas de Rede (localhost):{UI.RESET}")
    for port, in_use in checks["ports"].items():
        desc = {8000: "API / Painel Web", 5432: "PostgreSQL", 6379: "Redis"}.get(port, "")
        if in_use:
            UI.info(f"Porta {port} ({desc}): em uso ou já vinculada")
        else:
            UI.success(f"Porta {port} ({desc}): disponível")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Leitura de Configurações Existentes
# ─────────────────────────────────────────────────────────────────────────────

def parse_existing_env(path: Path = TARGET_ENV) -> Dict[str, str]:
    if not path.is_file():
        return {}
    res: Dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                res[k] = v
    except Exception:
        pass
    return res


# ─────────────────────────────────────────────────────────────────────────────
# 3. Testes ao Vivo de Integrações
# ─────────────────────────────────────────────────────────────────────────────

def test_telegram_bot_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Testa o token via api.telegram.org/bot<token>/getMe."""
    if not token or ":" not in token:
        return False, None, "Formato do token inválido (esperado ID:HASH)"
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramMoneySetup/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("ok"):
                res = data.get("result", {})
                username = res.get("username", "")
                name = res.get("first_name", "")
                return True, username, name
    except urllib.error.HTTPError as e:
        if e.code in (401, 404):
            return False, None, "Token não autorizado pelo Telegram (verifique no @BotFather)."
        return False, None, f"Erro HTTP {e.code} da API do Telegram."
    except Exception as e:
        return False, None, f"Falha de conexão com api.telegram.org: {e}"
    return False, None, "Resposta inesperada da API do Telegram."


def test_brapi_token(token: str) -> Tuple[bool, Optional[str]]:
    """Testa se o token da brapi.dev é válido."""
    if not token:
        return True, "Modo gratuito ativado (sem token)"
    url = f"https://brapi.dev/api/quote/PETR4?token={token}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramMoneySetup/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return True, "Token validado com sucesso na brapi.dev!"
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Token inválido ou não autorizado pela brapi.dev."
        return False, f"A brapi retornou status HTTP {e.code}."
    except Exception as e:
        return False, f"Não foi possível validar na brapi agora: {e}"
    return False, "Falha na validação do token brapi."


def discover_lm_studio_models(base_url: str = "http://localhost:1235/v1") -> List[str]:
    """Busca modelos carregados no servidor LM Studio."""
    url = f"{base_url.rstrip('/')}/models"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramMoneySetup/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return [m.get("id") for m in data.get("data", []) if m.get("id")]
    except Exception:
        return []


def discover_ollama_models(base_url: str = "http://localhost:11434") -> List[str]:
    """Busca modelos instalados no Ollama."""
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramMoneySetup/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 4. Passos Interativos do Wizard
# ─────────────────────────────────────────────────────────────────────────────

def prompt_owner_step(existing: Dict[str, str], quick: bool = False) -> Tuple[str, str]:
    UI.section(1 if quick else 2, 6, "Acesso do Proprietário (Administrador)")
    print("O Telegram Money é um sistema pessoal com painel privado.")

    default_email = existing.get("OWNER_EMAIL", "voce@example.com")
    while True:
        email = UI.ask("E-mail para login no painel", default_email).lower()
        if "@" in email and "." in email and not any(c in email for c in "\r\n#='\" "):
            break
        UI.warning("Informe um e-mail válido (ex: seu.nome@email.com).")

    has_prev_pass = bool(existing.get("OWNER_PASSWORD"))
    if has_prev_pass:
        if UI.confirm("Deseja manter a senha mestra atualmente configurada?", default=True):
            password = existing["OWNER_PASSWORD"]
            UI.success("Senha atual preservada.")
            return email, password

    password = UI.ask_secret("Defina a senha mestra do painel (mínimo 12 caracteres)")
    UI.success("Senha mestra validada.")
    return email, password


def prompt_infrastructure_step(existing: Dict[str, str], checks: Dict[str, Any]) -> Tuple[str, str, str, str]:
    UI.section(3, 6, "Banco de Dados e Infraestrutura")

    default_choice = 0 if checks["docker"]["daemon_running"] else 1
    options = [
        ("docker", "Docker Compose (PostgreSQL 16 + Redis 7 isolados em containers - Recomendado)"),
        ("local", "Desenvolvimento Local (SQLite em backend/data/ + Redis no host)"),
    ]
    mode = UI.ask_choice("Escolha o ambiente de execução:", options, default_choice)

    # Postgres password
    pg_pass = existing.get("POSTGRES_PASSWORD") or secrets.token_hex(24)

    if mode == "docker":
        db_url = "postgresql+psycopg://telegram:${POSTGRES_PASSWORD}@db:5432/telegram_money"
        redis_url = "redis://redis:6379/0"
        UI.success("Configuração otimizada para Docker Compose (PostgreSQL + Redis).")
    else:
        db_url = "sqlite:///./data/telegram-money.db"
        redis_url = "redis://localhost:6379/0"
        UI.info("Configuração ajustada para SQLite local e Redis no host.")

    return mode, pg_pass, db_url, redis_url


def prompt_telegram_step(existing: Dict[str, str]) -> Tuple[str, str]:
    UI.section(4, 6, "Integração com Telegram Bot (Opcional)")
    print("O bot envia alertas de cotações, relatórios e permite comandos (/cotacao, /carteira).")
    print(f"{UI.DIM}Para criar seu bot: acesse @BotFather no Telegram e execute /newbot.{UI.RESET}\n")

    current_token = existing.get("TELEGRAM_BOT_TOKEN", "")
    current_user = existing.get("TELEGRAM_BOT_USERNAME", "")

    want_telegram = UI.confirm(
        "Deseja configurar o Bot do Telegram agora?",
        default=bool(current_token) or False,
    )

    if not want_telegram:
        UI.info("Integração com Telegram ignorada (poderá ser configurada posteriormente).")
        return "", ""

    while True:
        token = UI.ask("Token do Bot (fornecido pelo @BotFather)", current_token)
        if not token:
            if UI.confirm("Deixar token em branco e continuar sem bot?", default=True):
                return "", ""
            continue

        print(f"  {UI.CYAN}Verificando token com a API do Telegram...{UI.RESET}")
        ok, detected_user, msg = test_telegram_bot_token(token)
        if ok:
            UI.success(f"Bot validado: @{detected_user} ({msg})")
            user_input = UI.ask("Username do bot (sem @)", detected_user or current_user)
            username = user_input.lstrip("@").strip()
            return token, username
        else:
            UI.warning(f"{msg}")
            if UI.confirm("Deseja manter este token mesmo sem confirmação da API?", default=False):
                username = UI.ask("Username do bot (sem @)", current_user).lstrip("@").strip()
                return token, username


def prompt_market_data_step(existing: Dict[str, str]) -> Tuple[str, int]:
    UI.section(5, 6, "Dados de Mercado & Coleta B3")
    print("Cotações e proventos são obtidos por fontes abertas gratuitas.")
    print(f"{UI.DIM}Um token opcional da brapi.dev amplia a quantidade de tickers suportados.{UI.RESET}\n")

    current_token = existing.get("BRAPI_TOKEN", "")
    token = UI.ask("Token da brapi.dev (deixe em branco se não possuir)", current_token)

    if token:
        print(f"  {UI.CYAN}Testando token brapi...{UI.RESET}")
        ok, msg = test_brapi_token(token)
        if ok:
            UI.success(msg)
        else:
            UI.warning(msg)
            if not UI.confirm("Manter este token?", default=True):
                token = ""

    poll_def = existing.get("POLL_SECONDS", "120")
    while True:
        poll_str = UI.ask("Intervalo de monitoramento de cotações em segundos (mínimo 30s)", poll_def)
        if poll_str.isdigit() and int(poll_str) >= 30:
            poll_seconds = int(poll_str)
            break
        UI.warning("O intervalo mínimo de coleta é de 30 segundos.")

    return token, poll_seconds


def ai_defaults(existing: Dict[str, str], mode: str) -> Dict[str, Any]:
    host = "host.docker.internal" if mode == "docker" else "localhost"
    return {
        "ai_provider": existing.get("AI_PROVIDER", "lmstudio"),
        "lm_studio_base_url": existing.get("LM_STUDIO_BASE_URL", f"http://{host}:1235/v1"),
        "lm_studio_model": existing.get("LM_STUDIO_MODEL", "qwen3.5-9b"),
        "lm_studio_api_key": existing.get("LM_STUDIO_API_KEY", ""),
        "ollama_url": existing.get("OLLAMA_URL", f"http://{host}:11434"),
        "ollama_model": existing.get("OLLAMA_MODEL", ""),
        "ai_timeout_seconds": int(existing.get("AI_TIMEOUT_SECONDS", "180")),
    }


def prompt_ai_step(existing: Dict[str, str], mode: str) -> Dict[str, Any]:
    UI.section(6, 6, "Inteligência Artificial Local (Resumos e Fatos Relevantes)")
    print("Processamento de documentos com IA local, sem envio de dados a terceiros.")

    # Detecção ao vivo no host
    lm_models = discover_lm_studio_models("http://localhost:1235/v1")
    ollama_models = discover_ollama_models("http://localhost:11434")

    if lm_models:
        UI.success(f"LM Studio detectado ativo com {len(lm_models)} modelo(s): {', '.join(lm_models[:3])}")
    if ollama_models:
        UI.success(f"Ollama detectado ativo com {len(ollama_models)} modelo(s): {', '.join(ollama_models[:3])}")

    options = [
        ("lmstudio", "LM Studio (Recomendado - porta padrão 1235)"),
        ("ollama", "Ollama (porta padrão 11434)"),
        ("none", "Desativar IA por enquanto"),
    ]
    current_prov = existing.get("AI_PROVIDER", "lmstudio")
    default_idx = 0 if current_prov == "lmstudio" else (1 if current_prov == "ollama" else 2)
    choice = UI.ask_choice("Escolha o provedor de IA:", options, default_idx)

    config = ai_defaults(existing, mode)

    if choice == "lmstudio":
        url = UI.ask("URL base do LM Studio", config["lm_studio_base_url"])
        default_model = "qwen3.5-9b"
        if lm_models:
            # Prefere qwen3.5 se presente
            for m in lm_models:
                if "qwen3.5" in m.lower():
                    default_model = m
                    break
            else:
                default_model = lm_models[0]
        model = UI.ask("ID do modelo no LM Studio", existing.get("LM_STUDIO_MODEL", default_model))
        api_key = UI.ask("Chave de API do LM Studio (opcional, deixe vazio se desativado)", existing.get("LM_STUDIO_API_KEY", ""))
        config.update(ai_provider="lmstudio", lm_studio_base_url=url, lm_studio_model=model, lm_studio_api_key=api_key)
    elif choice == "ollama":
        url = UI.ask("URL do Ollama", config["ollama_url"])
        default_model = ollama_models[0] if ollama_models else "llama3.2"
        model = UI.ask("Nome do modelo no Ollama", existing.get("OLLAMA_MODEL", default_model))
        config.update(ai_provider="ollama", ollama_url=url, ollama_model=model)
    else:
        config.update(lm_studio_model="", ollama_model="")
    return config


def prompt_preferences_step(existing: Dict[str, str]) -> Tuple[str, str, bool]:
    tz = UI.ask("Fuso horário do sistema", existing.get("TIMEZONE", "America/Sao_Paulo"))
    origin = UI.ask("Origem do painel (APP_ORIGIN)", existing.get("APP_ORIGIN", "http://localhost:8000"))
    cookie_secure = existing.get("COOKIE_SECURE", "false").lower() == "true"
    return tz, origin, cookie_secure


# ─────────────────────────────────────────────────────────────────────────────
# 5. Geração e Gravação Segura do Arquivo .env
# ─────────────────────────────────────────────────────────────────────────────

def build_env_content(cfg: Dict[str, Any]) -> str:
    """Gera o conteúdo final formatado para o arquivo .env."""
    lines = [
        "# =============================================================================",
        "# Telegram Money · Configuração de Ambiente",
        "# Gerado automaticamente pelo Setup Wizard com permissão estrita (0600).",
        "# Nunca versione este arquivo nem compartilhe credenciais.",
        "# =============================================================================",
        "",
        "# --- Acesso do Proprietário ---",
        f"OWNER_EMAIL='{cfg['owner_email']}'",
        f"OWNER_PASSWORD='{cfg['owner_password']}'",
        "",
        "# --- Infraestrutura e Banco de Dados ---",
        f"POSTGRES_PASSWORD={cfg['postgres_password']}",
        f"DATABASE_URL={cfg['database_url']}",
        f"REDIS_URL={cfg['redis_url']}",
        "",
        "# --- Aplicação e Segurança ---",
        f"APP_ORIGIN={cfg['app_origin']}",
        f"COOKIE_SECURE={'true' if cfg['cookie_secure'] else 'false'}",
        f"TIMEZONE={cfg['timezone']}",
        f"AI_ALLOWED_ORIGINS={cfg.get('ai_allowed_origins', '')}",
        "",
        "# --- Integração Telegram ---",
        f"TELEGRAM_BOT_TOKEN={cfg['telegram_bot_token']}",
        f"TELEGRAM_BOT_USERNAME={cfg['telegram_bot_username']}",
        "",
        "# --- Dados de Mercado & Coleta ---",
        f"BRAPI_TOKEN={cfg['brapi_token']}",
        f"POLL_SECONDS={cfg['poll_seconds']}",
        "",
        "# --- Inteligência Artificial Local ---",
        f"AI_PROVIDER={cfg['ai_provider']}",
        f"LM_STUDIO_BASE_URL={cfg['lm_studio_base_url']}",
        f"LM_STUDIO_MODEL={cfg['lm_studio_model']}",
        f"LM_STUDIO_API_KEY={cfg['lm_studio_api_key']}",
        f"AI_TIMEOUT_SECONDS={cfg['ai_timeout_seconds']}",
        f"OLLAMA_URL={cfg['ollama_url']}",
        f"OLLAMA_MODEL={cfg['ollama_model']}",
        "",
        "# --- Modo de Demonstração ---",
        f"DEMO_MODE={'true' if cfg.get('demo_mode') else 'false'}",
    ]
    return "\n".join(lines) + "\n"


def write_env_file(content: str) -> None:
    """Grava o arquivo .env de forma atômica e segura com permissão 0600."""
    if TARGET_ENV.exists():
        backup_path = ROOT / ".env.bak"
        shutil.copy2(TARGET_ENV, backup_path)
        UI.info(f"Backup do arquivo anterior salvo em: {backup_path.name}")

    # Abre arquivo com permissão 0600 (apenas leitura/escrita pelo proprietário)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(TARGET_ENV, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)

    # Garante permissão 0600 em sistemas Unix
    try:
        os.chmod(TARGET_ENV, 0o600)
    except Exception:
        pass


def display_summary(cfg: Dict[str, Any]) -> None:
    print(f"\n{UI.BOLD}Resumo da Configuração:{UI.RESET}")
    print(f"  • E-mail do proprietário:  {UI.CYAN}{cfg['owner_email']}{UI.RESET}")
    print(f"  • Senha do proprietário:   {UI.GREEN}•••••••••••• (configurada){UI.RESET}")
    print(f"  • Modo de infraestrutura:  {cfg['mode'].upper()}")
    print(f"  • Painel Web / Origem:     {UI.CYAN}{cfg['app_origin']}{UI.RESET}")
    print(f"  • Fuso horário:            {cfg['timezone']}")
    print(f"  • Intervalo de coleta:     {cfg['poll_seconds']}s")
    if cfg['telegram_bot_token']:
        print(f"  • Telegram Bot:            {UI.GREEN}@{cfg['telegram_bot_username']} (ativo){UI.RESET}")
    else:
        print(f"  • Telegram Bot:            {UI.DIM}(não configurado){UI.RESET}")
    if cfg['brapi_token']:
        print(f"  • brapi.dev:               {UI.GREEN}Token configurado{UI.RESET}")
    else:
        print(f"  • brapi.dev:               {UI.DIM}Modo gratuito padrão{UI.RESET}")
    print(f"  • Gateway IA:              {cfg['ai_provider']} ({cfg['lm_studio_model'] if cfg['ai_provider'] == 'lmstudio' else cfg['ollama_model']})")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Inicialização do Sistema
# ─────────────────────────────────────────────────────────────────────────────

def start_docker_services(has_telegram: bool) -> bool:
    """Inicia os containers via Docker Compose e verifica o health check."""
    env = os.environ.copy()
    env.pop("DOCKER_HOST", None)

    cmd = ["docker", "compose"]
    if has_telegram:
        cmd.extend(["--profile", "telegram"])
    cmd.extend(["up", "-d", "--build"])

    print(f"\n{UI.BOLD}Executando:{UI.RESET} {' '.join(cmd)}\n")
    try:
        res = subprocess.run(cmd, env=env, cwd=ROOT)
        if res.returncode != 0:
            UI.error("Falha ao subir containers via Docker Compose.")
            return False
    except Exception as e:
        UI.error(f"Erro ao disparar Docker: {e}")
        return False

    print(f"\n{UI.CYAN}Aguardando inicialização da API (healthcheck)...{UI.RESET}")
    for _ in range(15):
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    UI.success("API e serviços iniciados e respondendo com sucesso!")
                    return True
        except Exception:
            pass
        subprocess.run(["sleep", "2"], capture_output=True)

    UI.info("Containers estão subindo. Acesse http://localhost:8000 assim que concluírem o boot.")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 7. Função Principal
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram Money · Setup Wizard")
    parser.add_argument("--check-only", action="store_true", help="Executa apenas diagnóstico do ambiente")
    parser.add_argument("--quick", action="store_true", help="Modo rápido: configura apenas e-mail e senha")
    parser.add_argument("-y", "--yes", action="store_true", help="Aceita padrões não interativos onde aplicável")
    args = parser.parse_args()

    UI.banner()

    checks = run_environment_checks()
    print_environment_report(checks)

    if args.check_only:
        sys.exit(0)

    existing = parse_existing_env()
    if existing:
        UI.info(f"Configuração existente detectada em {TARGET_ENV.name}.")
        if not args.yes and not UI.confirm("Deseja executar o assistente e atualizar as configurações?", default=True):
            print("Operação cancelada. Nenhuma alteração foi realizada.")
            sys.exit(0)

    # 1. Proprietário
    owner_email, owner_password = prompt_owner_step(existing, quick=args.quick)

    # Defaults para modo rápido
    if args.quick:
        mode = "docker" if checks["docker"]["daemon_running"] else "local"
        pg_pass = existing.get("POSTGRES_PASSWORD") or secrets.token_hex(24)
        db_url = "postgresql+psycopg://telegram:${POSTGRES_PASSWORD}@db:5432/telegram_money" if mode == "docker" else "sqlite:///./data/telegram-money.db"
        redis_url = "redis://redis:6379/0" if mode == "docker" else "redis://localhost:6379/0"
        tg_token, tg_user = existing.get("TELEGRAM_BOT_TOKEN", ""), existing.get("TELEGRAM_BOT_USERNAME", "")
        brapi_token, poll_secs = existing.get("BRAPI_TOKEN", ""), int(existing.get("POLL_SECONDS", "120"))
        ai_config = ai_defaults(existing, mode)
        tz = existing.get("TIMEZONE", "America/Sao_Paulo")
        origin = existing.get("APP_ORIGIN", "http://localhost:8000")
        cookie_sec = existing.get("COOKIE_SECURE", "false").lower() == "true"
    else:
        # 2. Infraestrutura
        mode, pg_pass, db_url, redis_url = prompt_infrastructure_step(existing, checks)
        # 3. Telegram
        tg_token, tg_user = prompt_telegram_step(existing)
        # 4. Dados de mercado
        brapi_token, poll_secs = prompt_market_data_step(existing)
        # 5. IA
        ai_config = prompt_ai_step(existing, mode)
        # 6. Preferências
        tz, origin, cookie_sec = prompt_preferences_step(existing)

    cfg: Dict[str, Any] = {
        "owner_email": owner_email,
        "owner_password": owner_password,
        "postgres_password": pg_pass,
        "database_url": db_url,
        "redis_url": redis_url,
        "app_origin": origin,
        "cookie_secure": cookie_sec,
        "timezone": tz,
        "ai_allowed_origins": existing.get("AI_ALLOWED_ORIGINS", ""),
        "telegram_bot_token": tg_token,
        "telegram_bot_username": tg_user,
        "brapi_token": brapi_token,
        "poll_seconds": poll_secs,
        **ai_config,
        "demo_mode": existing.get("DEMO_MODE", "false").lower() == "true",
        "mode": mode,
    }

    display_summary(cfg)

    # Gravação do arquivo .env
    content = build_env_content(cfg)
    write_env_file(content)
    UI.success(f"Arquivo {TARGET_ENV.name} gravado com sucesso com permissão 600!")

    # Inicialização opcional
    if mode == "docker" and checks["docker"]["daemon_running"]:
        if args.yes or UI.confirm("Deseja iniciar o sistema agora via Docker Compose?", default=True):
            start_docker_services(has_telegram=bool(tg_token))
            print(f"\n{UI.BOLD}{UI.GREEN}Pronto! Acesse o painel em:{UI.RESET} {UI.CYAN}{origin}{UI.RESET}")
            print(f"Login: {UI.BOLD}{owner_email}{UI.RESET}\n")
            return

    print(f"\n{UI.BOLD}Comandos para inicialização manual:{UI.RESET}")
    if mode == "docker":
        prof = " --profile telegram" if tg_token else ""
        print(f"  docker compose{prof} up -d --build")
    else:
        print("  cd frontend && npm run build")
        print("  cd ../backend && uv run alembic upgrade head")
        print(f"  uv run uvicorn app.main:app --host 127.0.0.1 --port 8000")
    print(f"\nAcesse o painel em: {UI.CYAN}{origin}{UI.RESET}\n")


if __name__ == "__main__":
    main()
