#!/usr/bin/env bash
set -Eeuo pipefail

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*"
}

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    log "Configuration manquante: ${name}"
    exit 1
  fi
}

require_env POSTGRES_SERVER
require_env POSTGRES_PORT
require_env POSTGRES_DB
require_env POSTGRES_USER
require_env POSTGRES_PASSWORD
require_env MINIO_ENDPOINT
require_env MINIO_ACCESS_KEY
require_env MINIO_SECRET_KEY
require_env MINIO_BUCKET
require_env BACKUP_ENCRYPTION_PASSPHRASE

secure_archive() {
  local archive="$1"
  chmod 600 "${archive}"
  if [ -n "${backup_owner}" ]; then
    chown "${backup_owner}" "${archive}" || true
  fi
}

if [ "${BACKUP_ENCRYPTION_PASSPHRASE}" = "change-this-long-passphrase" ]; then
  log "BACKUP_ENCRYPTION_PASSPHRASE doit être remplacée avant utilisation."
  exit 1
fi

BACKUP_ROOT="${BACKUP_ROOT:-/backups}"
DAILY_DIR="${BACKUP_ROOT}/daily"
WEEKLY_DIR="${BACKUP_ROOT}/weekly"
WORK_ROOT="${BACKUP_ROOT}/.tmp"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_NAME="keneyalab-${TIMESTAMP}"
WORK_DIR="${WORK_ROOT}/${BACKUP_NAME}"
TARBALL="${WORK_ROOT}/${BACKUP_NAME}.tar.gz"
FINAL_DAILY="${DAILY_DIR}/${BACKUP_NAME}.tar.gz.gpg"
backup_owner="$(stat -c '%u:%g' "${BACKUP_ROOT}" 2>/dev/null || true)"

cleanup() {
  rm -rf "${WORK_DIR}" "${TARBALL}"
}
trap cleanup EXIT

mkdir -p "${DAILY_DIR}" "${WEEKLY_DIR}" "${WORK_DIR}/minio" "${WORK_ROOT}"
if [ -n "${backup_owner}" ]; then
  chown "${backup_owner}" "${DAILY_DIR}" "${WEEKLY_DIR}" "${WORK_ROOT}" || true
fi

log "Démarrage de la sauvegarde ${BACKUP_NAME}"

export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump \
  -h "${POSTGRES_SERVER}" \
  -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  -Fc \
  --no-owner \
  --file "${WORK_DIR}/db.dump"
log "Sauvegarde PostgreSQL terminée"

mc alias set keneyalab-minio "http://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" >/dev/null
mc mb --ignore-existing "keneyalab-minio/${MINIO_BUCKET}" >/dev/null
mc mirror --overwrite "keneyalab-minio/${MINIO_BUCKET}" "${WORK_DIR}/minio" >/dev/null
log "Sauvegarde MinIO terminée"

cat > "${WORK_DIR}/manifest.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "backup_name": "${BACKUP_NAME}",
  "database": "${POSTGRES_DB}",
  "minio_bucket": "${MINIO_BUCKET}",
  "stack_name": "${STACK_NAME:-}",
  "tag": "${TAG:-}",
  "kind": "daily",
  "format_version": 1
}
EOF

tar -C "${WORK_ROOT}" -czf "${TARBALL}" "${BACKUP_NAME}"
gpg \
  --batch \
  --yes \
  --pinentry-mode loopback \
  --passphrase "${BACKUP_ENCRYPTION_PASSPHRASE}" \
  --symmetric \
  --cipher-algo AES256 \
  --output "${FINAL_DAILY}" \
  "${TARBALL}"
secure_archive "${FINAL_DAILY}"
log "Archive chiffrée créée: ${FINAL_DAILY}"

if [ "$(date +%u)" = "7" ]; then
  cp "${FINAL_DAILY}" "${WEEKLY_DIR}/"
  secure_archive "${WEEKLY_DIR}/$(basename "${FINAL_DAILY}")"
  log "Copie hebdomadaire créée"
fi

find "${DAILY_DIR}" -maxdepth 1 -type f -name 'keneyalab-*.tar.gz.gpg' \
  -printf '%T@ %p\n' | sort -rn | awk 'NR>14 {print $2}' | xargs -r rm -f
find "${WEEKLY_DIR}" -maxdepth 1 -type f -name 'keneyalab-*.tar.gz.gpg' \
  -printf '%T@ %p\n' | sort -rn | awk 'NR>8 {print $2}' | xargs -r rm -f
log "Rétention appliquée: 14 journalières, 8 hebdomadaires"
log "Sauvegarde terminée"
