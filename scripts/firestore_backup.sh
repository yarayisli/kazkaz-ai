#!/usr/bin/env bash
set -euo pipefail

: "${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID gerekli}"
: "${FIRESTORE_BACKUP_BUCKET:?FIRESTORE_BACKUP_BUCKET gerekli}"
: "${BACKUP_VERIFY_DOCUMENT_PATH:?BACKUP_VERIFY_DOCUMENT_PATH gerekli (sabit bir doğrulama belgesi)}"

command -v gcloud >/dev/null || { echo "gcloud bulunamadı." >&2; exit 5; }
python_bin="${PYTHON_BIN:-python3}"
command -v "$python_bin" >/dev/null || { echo "$python_bin bulunamadı." >&2; exit 5; }
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
database_id="${FIRESTORE_DATABASE_ID:-(default)}"
evidence_dir="${BACKUP_EVIDENCE_DIR:-${repo_dir}/outputs/backup-evidence}"
mkdir -p "$evidence_dir"

backup_date="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
bucket="${FIRESTORE_BACKUP_BUCKET#gs://}"
target="gs://${bucket%/}/kazkaz/${backup_date}"
operation_file="${evidence_dir}/${backup_date}-export-operation.json"
evidence_file="${evidence_dir}/${backup_date}-backup.json"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
started_epoch="$(date -u +%s)"

fingerprint="$($python_bin "$repo_dir/scripts/backup_restore_evidence.py" fingerprint \
  --project "$FIREBASE_PROJECT_ID" --database "$database_id" \
  --document "$BACKUP_VERIFY_DOCUMENT_PATH")"
if [[ ! "$fingerprint" =~ ^[0-9a-f]{64}$ ]]; then
  echo "Doğrulama belgesi parmak izi üretilemedi." >&2
  exit 6
fi

gcloud firestore export "$target" --project "$FIREBASE_PROJECT_ID" \
  --database "$database_id" --quiet --format=json >"$operation_file"
metadata_uri="$(gcloud storage ls --recursive "${target}/" | awk '/\.overall_export_metadata$/ {print; exit}')"
if [[ -z "$metadata_uri" || "$metadata_uri" != "${target}/"* ]]; then
  echo "Export tamamlandı ancak .overall_export_metadata bulunamadı; yedek kanıtlanamadı." >&2
  exit 6
fi
completed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
duration_seconds="$(( $(date -u +%s) - started_epoch ))"

"$python_bin" "$repo_dir/scripts/backup_restore_evidence.py" backup \
  --project "$FIREBASE_PROJECT_ID" --database "$database_id" --uri "$target" \
  --metadata-uri "$metadata_uri" --started-at "$started_at" --completed-at "$completed_at" \
  --duration-seconds "$duration_seconds" --document "$BACKUP_VERIFY_DOCUMENT_PATH" \
  --sha256 "$fingerprint" --output "$evidence_file"
gcloud storage cp "$evidence_file" "${target}/backup-evidence.json" >/dev/null
echo "Firestore yedeği ve doğrulama kanıtı oluşturuldu: $target"
echo "Kanıt: $evidence_file"
