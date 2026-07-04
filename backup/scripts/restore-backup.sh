#!/usr/bin/env bash
set -Eeuo pipefail

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*"
}

usage() {
  cat <<'EOF'
Usage:
  restore-backup.sh /backups/daily/keneyalab-YYYYMMDD-HHMMSS.tar.gz.gpg --confirm

This destructively replaces the configured PostgreSQL database and MinIO bucket.
Stop backend/frontend/prestart before running restore.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ARCHIVE="${1:-}"
CONFIRM="${2:-}"
if [ -z "${ARCHIVE}" ] || [ "${CONFIRM}" != "--confirm" ]; then
  usage
  exit 1
fi
if [ ! -f "${ARCHIVE}" ]; then
  log "Archive introuvable: ${ARCHIVE}"
  exit 1
fi

for name in POSTGRES_SERVER POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD MINIO_ENDPOINT MINIO_ACCESS_KEY MINIO_SECRET_KEY MINIO_BUCKET BACKUP_ENCRYPTION_PASSPHRASE; do
  if [ -z "${!name:-}" ]; then
    log "Configuration manquante: ${name}"
    exit 1
  fi
done

RESTORE_ROOT="$(mktemp -d)"
DECRYPTED="${RESTORE_ROOT}/backup.tar.gz"
cleanup() {
  rm -rf "${RESTORE_ROOT}"
}
trap cleanup EXIT

log "Déchiffrement de ${ARCHIVE}"
gpg \
  --batch \
  --yes \
  --pinentry-mode loopback \
  --passphrase "${BACKUP_ENCRYPTION_PASSPHRASE}" \
  --decrypt \
  --output "${DECRYPTED}" \
  "${ARCHIVE}"

tar -C "${RESTORE_ROOT}" -xzf "${DECRYPTED}"
BACKUP_DIR="$(find "${RESTORE_ROOT}" -mindepth 1 -maxdepth 1 -type d -name 'keneyalab-*' | head -n 1)"
if [ -z "${BACKUP_DIR}" ] || [ ! -f "${BACKUP_DIR}/db.dump" ]; then
  log "Archive invalide: db.dump absent"
  exit 1
fi

export PGPASSWORD="${POSTGRES_PASSWORD}"
log "Remplacement de la base PostgreSQL ${POSTGRES_DB}"
psql \
  -h "${POSTGRES_SERVER}" \
  -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" \
  -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();"
dropdb \
  -h "${POSTGRES_SERVER}" \
  -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" \
  --if-exists \
  "${POSTGRES_DB}"
createdb \
  -h "${POSTGRES_SERVER}" \
  -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" \
  "${POSTGRES_DB}"
pg_restore \
  -h "${POSTGRES_SERVER}" \
  -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  --no-owner \
  "${BACKUP_DIR}/db.dump"

log "Remplacement du bucket MinIO ${MINIO_BUCKET}"
mc alias set keneyalab-minio "http://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" >/dev/null
mc mb --ignore-existing "keneyalab-minio/${MINIO_BUCKET}" >/dev/null
mc rm --recursive --force "keneyalab-minio/${MINIO_BUCKET}" >/dev/null || true
if [ -d "${BACKUP_DIR}/minio" ]; then
  mc mirror --overwrite "${BACKUP_DIR}/minio" "keneyalab-minio/${MINIO_BUCKET}" >/dev/null
fi

log "Restauration terminée"
