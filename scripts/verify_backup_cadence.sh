#!/usr/bin/env bash
set -euo pipefail

: "${PREVIOUS_BACKUP_EVIDENCE_FILE:?PREVIOUS_BACKUP_EVIDENCE_FILE gerekli}"
: "${CURRENT_BACKUP_EVIDENCE_FILE:?CURRENT_BACKUP_EVIDENCE_FILE gerekli}"
: "${RPO_TARGET_HOURS:?RPO_TARGET_HOURS gerekli}"
if [[ ! "$RPO_TARGET_HOURS" =~ ^[0-9]+([.][0-9]+)?$ ]] || [[ "$RPO_TARGET_HOURS" == "0" ]]; then
  echo "RPO_TARGET_HOURS pozitif sayı olmalıdır." >&2
  exit 2
fi

python_bin="${PYTHON_BIN:-python3}"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
evidence_dir="${BACKUP_EVIDENCE_DIR:-${repo_dir}/outputs/backup-evidence}"
mkdir -p "$evidence_dir"
evidence_file="${evidence_dir}/$(date -u +%Y-%m-%dT%H-%M-%SZ)-backup-cadence.json"

"$python_bin" "$repo_dir/scripts/backup_restore_evidence.py" cadence \
  --previous "$PREVIOUS_BACKUP_EVIDENCE_FILE" --current "$CURRENT_BACKUP_EVIDENCE_FILE" \
  --target-hours "$RPO_TARGET_HOURS" --output "$evidence_file"
observed="$($python_bin "$repo_dir/scripts/backup_restore_evidence.py" read \
  --file "$evidence_file" --field measurement.observedIntervalHours)"
echo "Ardışık yedek aralığı RPO hedefini karşıladı: ${observed} saat <= ${RPO_TARGET_HOURS} saat"
echo "Kanıt: $evidence_file"
echo "Canlı hazırlık için BACKUP_MAX_OBSERVED_INTERVAL_HOURS=$observed değerini kaydedin."
echo "Canlı hazırlık için BACKUP_SCHEDULE_VERIFIED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ) değerini kaydedin."
