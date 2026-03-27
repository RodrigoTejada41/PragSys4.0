#!/usr/bin/env bash

set -Eeuo pipefail

DEPLOY_ENV=""
TARGET_BRANCH=""
APP_DIR=""
HEALTHCHECK_URL=""
COMPOSE_FILE="docker-compose.yml"
SERVICES=("syspragas" "whatsapp-bridge")
BACKUP_DIR=""
RELEASES_DIR=""
ROLLBACK_BACKUP_PATH=""
PREVIOUS_COMMIT=""
DEPLOYED_COMMIT=""
ROLLBACK_ON_ERROR=true

log() {
  printf '[%s] [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${DEPLOY_ENV:-deploy}" "$*"
}

fail() {
  log "ERRO: $*"
  exit 1
}

usage() {
  cat <<'EOF'
Uso:
  ./deploy/deploy.sh --env <dev|prod> --branch <branch> --app-dir <path>

Opcoes:
  --env <value>          Ambiente logico do deploy.
  --branch <value>       Branch que sera publicada.
  --app-dir <value>      Diretorio do checkout da aplicacao na VPS.
  --health-url <value>   URL de health check. Padrao: http://127.0.0.1:8000/health
  --compose-file <value> Arquivo Compose a ser usado. Padrao: docker-compose.yml
  --no-rollback          Desabilita rollback automatico do codigo em caso de falha.
EOF
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Comando obrigatorio nao encontrado: $1"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --env)
        DEPLOY_ENV="$2"
        shift 2
        ;;
      --branch)
        TARGET_BRANCH="$2"
        shift 2
        ;;
      --app-dir)
        APP_DIR="$2"
        shift 2
        ;;
      --health-url)
        HEALTHCHECK_URL="$2"
        shift 2
        ;;
      --compose-file)
        COMPOSE_FILE="$2"
        shift 2
        ;;
      --no-rollback)
        ROLLBACK_ON_ERROR=false
        shift
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

  [[ -n "$DEPLOY_ENV" ]] || fail "Informe --env"
  [[ -n "$TARGET_BRANCH" ]] || fail "Informe --branch"
  [[ -n "$APP_DIR" ]] || fail "Informe --app-dir"
}

prepare_paths() {
  HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8000/health}"
  BACKUP_DIR="${APP_DIR}/deploy/backups/${DEPLOY_ENV}"
  RELEASES_DIR="${APP_DIR}/deploy/releases/${DEPLOY_ENV}"
  mkdir -p "$BACKUP_DIR" "$RELEASES_DIR"
}

backup_database() {
  local timestamp backup_path
  timestamp="$(date '+%Y%m%d_%H%M%S')"
  backup_path="${BACKUP_DIR}/predeploy_${DEPLOY_ENV}_${timestamp}.db"

  if ! docker container inspect syspragas >/dev/null 2>&1; then
    log "Container syspragas ainda nao existe. Backup do banco sera ignorado."
    return 0
  fi

  log "Gerando backup preventivo do banco em ${backup_path}"
  docker cp syspragas:/data/syspragas.db "$backup_path"
  ROLLBACK_BACKUP_PATH="$backup_path"
}

write_release_metadata() {
  local metadata_file
  metadata_file="${RELEASES_DIR}/latest_release.env"
  cat >"$metadata_file" <<EOF
DEPLOY_ENV=${DEPLOY_ENV}
TARGET_BRANCH=${TARGET_BRANCH}
PREVIOUS_COMMIT=${PREVIOUS_COMMIT}
DEPLOYED_COMMIT=${DEPLOYED_COMMIT}
ROLLBACK_DB_PATH=${ROLLBACK_BACKUP_PATH}
DEPLOYED_AT=$(date '+%Y-%m-%dT%H:%M:%S%z')
EOF
}

run_compose() {
  docker compose -f "$COMPOSE_FILE" up --build -d "${SERVICES[@]}"
}

health_check() {
  local attempt
  for attempt in {1..20}; do
    if curl --fail --silent --show-error "$HEALTHCHECK_URL" >/dev/null; then
      log "Health check concluido com sucesso em ${HEALTHCHECK_URL}"
      return 0
    fi
    log "Health check ainda indisponivel. Tentativa ${attempt}/20."
    sleep 5
  done
  fail "Health check falhou apos 20 tentativas."
}

rollback() {
  [[ "$ROLLBACK_ON_ERROR" == "true" ]] || return 0
  [[ -n "$PREVIOUS_COMMIT" ]] || return 0

  log "Iniciando rollback automatico para ${PREVIOUS_COMMIT}"
  git reset --hard "$PREVIOUS_COMMIT"
  run_compose

  if [[ -n "$ROLLBACK_BACKUP_PATH" && -f "$ROLLBACK_BACKUP_PATH" ]]; then
    log "Backup de banco preservado em ${ROLLBACK_BACKUP_PATH} para restauracao manual, se necessaria."
  fi
}

on_error() {
  local exit_code="$1"
  log "Deploy falhou com codigo ${exit_code}"
  rollback
  exit "$exit_code"
}

main() {
  parse_args "$@"
  prepare_paths

  require_command git
  require_command docker
  require_command curl

  [[ -d "$APP_DIR/.git" ]] || fail "Diretorio informado nao contem um checkout Git: $APP_DIR"
  [[ -f "$APP_DIR/$COMPOSE_FILE" ]] || fail "Arquivo Compose nao encontrado: $APP_DIR/$COMPOSE_FILE"

  trap 'on_error $?' ERR

  cd "$APP_DIR"

  PREVIOUS_COMMIT="$(git rev-parse HEAD)"
  log "Commit atual antes do deploy: ${PREVIOUS_COMMIT}"

  if [[ "$DEPLOY_ENV" == "prod" ]]; then
    backup_database
  fi

  log "Atualizando codigo a partir de origin/${TARGET_BRANCH}"
  git fetch origin "$TARGET_BRANCH" --tags
  git checkout "$TARGET_BRANCH"
  git reset --hard "origin/${TARGET_BRANCH}"
  DEPLOYED_COMMIT="$(git rev-parse HEAD)"
  log "Novo commit implantado: ${DEPLOYED_COMMIT}"

  log "Subindo servicos via Docker Compose"
  run_compose

  health_check
  write_release_metadata
  log "Deploy concluido com sucesso."
}

main "$@"
