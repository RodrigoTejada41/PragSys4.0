#!/usr/bin/env bash

set -Eeuo pipefail

APP_DIR=""
TARGET_COMMIT=""
COMPOSE_FILE="docker-compose.yml"

log() {
  printf '[%s] [rollback] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "ERRO: $*"
  exit 1
}

usage() {
  cat <<'EOF'
Uso:
  ./deploy/rollback.sh --app-dir <path> --commit <sha> [--compose-file <arquivo>]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-dir)
      APP_DIR="$2"
      shift 2
      ;;
    --commit)
      TARGET_COMMIT="$2"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Parametro desconhecido: $1"
      ;;
  esac
done

[[ -n "$APP_DIR" ]] || fail "Informe --app-dir"
[[ -n "$TARGET_COMMIT" ]] || fail "Informe --commit"

command -v git >/dev/null 2>&1 || fail "git nao encontrado"
command -v docker >/dev/null 2>&1 || fail "docker nao encontrado"

cd "$APP_DIR"
git reset --hard "$TARGET_COMMIT"
docker compose -f "$COMPOSE_FILE" up --build -d syspragas whatsapp-bridge
log "Rollback concluido para ${TARGET_COMMIT}"
