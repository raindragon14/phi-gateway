#!/usr/bin/env bash
#
# backup-db.sh — PhiGateway SQLite backup script
#
# Creates timestamped copies of the SQLite database, prunes backups
# older than 30 days, and logs activity to syslog.
#
# Usage:
#   ./scripts/backup-db.sh                    # uses defaults
#   DB_PATH=/app/data/phi.db ./backup-db.sh   # custom path
#
# Environment variables:
#   DB_PATH    — path to the SQLite database (default: ./data/phi.db)
#   BACKUP_DIR — backup destination directory (default: ./data/backups)
#   RETENTION  — days to keep backups (default: 30)
#

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DB_PATH="${DB_PATH:-$PROJECT_DIR/data/phi.db}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/data/backups}"
RETENTION="${RETENTION:-30}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/phi-${TIMESTAMP}.db"

# --- Pre-flight checks ---
if [ ! -f "$DB_PATH" ]; then
    logger -t phi-gateway-backup "ERROR: Database not found at ${DB_PATH}"
    echo "ERROR: Database not found at ${DB_PATH}" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

# --- Perform backup ---
cp "$DB_PATH" "$BACKUP_FILE"
chmod 640 "$BACKUP_FILE"

logger -t phi-gateway-backup "Backup created: ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"
echo "Backup created: ${BACKUP_FILE}"

# --- Prune old backups ---
find "$BACKUP_DIR" -name "phi-*.db" -type f -mtime "+${RETENTION}" -print \
    | while read -r old_backup; do
        rm -f "$old_backup"
        logger -t phi-gateway-backup "Pruned expired backup: ${old_backup}"
        echo "Pruned: ${old_backup}"
    done

# --- Summary ---
remaining="$(find "$BACKUP_DIR" -name "phi-*.db" -type f | wc -l)"
logger -t phi-gateway-backup "Backup complete. ${remaining} backups retained."
echo "Done. ${remaining} backups retained in ${BACKUP_DIR}."
