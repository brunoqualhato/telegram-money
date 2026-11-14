#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
destination="backups/telegram-money-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T db pg_dump -U telegram -d telegram_money -Fc > "$destination.partial"
mv "$destination.partial" "$destination"
printf 'Backup criado: %s\n' "$destination"
