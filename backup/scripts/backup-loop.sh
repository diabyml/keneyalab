#!/usr/bin/env bash
set -Eeuo pipefail

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*"
}

validate_time_part() {
  local name="$1"
  local value="$2"
  local min="$3"
  local max="$4"
  if ! [[ "${value}" =~ ^[0-9]+$ ]] || [ "${value}" -lt "${min}" ] || [ "${value}" -gt "${max}" ]; then
    log "${name} invalide: ${value}"
    exit 1
  fi
}

BACKUP_RUN_HOUR="${BACKUP_RUN_HOUR:-2}"
BACKUP_RUN_MINUTE="${BACKUP_RUN_MINUTE:-0}"
BACKUP_RUN_ON_START="${BACKUP_RUN_ON_START:-false}"

validate_time_part BACKUP_RUN_HOUR "${BACKUP_RUN_HOUR}" 0 23
validate_time_part BACKUP_RUN_MINUTE "${BACKUP_RUN_MINUTE}" 0 59

run_backup() {
  if ! /usr/local/bin/keneyalab-backup/run-backup.sh; then
    log "Échec de la sauvegarde. Nouvelle tentative au prochain horaire."
  fi
}

if [ "${BACKUP_RUN_ON_START}" = "true" ]; then
  run_backup
fi

while true; do
  now_epoch="$(date +%s)"
  target_time="$(printf '%02d:%02d:00' "${BACKUP_RUN_HOUR}" "${BACKUP_RUN_MINUTE}")"
  target_epoch="$(date -d "today ${target_time}" +%s)"
  if [ "${target_epoch}" -le "${now_epoch}" ]; then
    target_epoch="$(date -d "tomorrow ${target_time}" +%s)"
  fi
  sleep_seconds=$((target_epoch - now_epoch))
  log "Prochaine sauvegarde prévue dans ${sleep_seconds}s à ${target_time}"
  sleep "${sleep_seconds}"
  run_backup
done
