#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# != 1 || ! -f "$1" ]]; then
  printf 'Uso: bash scripts/restore.sh backups/arquivo.dump\n' >&2
  exit 1
fi
printf 'A restauração substitui o banco pessoal. Digite RESTAURAR: '
read -r confirmation
[[ "$confirmation" == RESTAURAR ]] || exit 1
docker compose stop api worker beat bot
docker compose exec -T db pg_restore -U telegram -d telegram_money --clean --if-exists --no-owner --exit-on-error < "$1"
docker compose up -d api worker beat
printf 'Banco restaurado. Se usar Telegram, execute docker compose --profile telegram up -d bot\n'
