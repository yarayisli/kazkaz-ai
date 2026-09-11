#!/usr/bin/env bash
set -euo pipefail

: "${RESTORE_TEST_PROJECT_ID:?RESTORE_TEST_PROJECT_ID gerekli}"
: "${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID gerekli (yedek kaynak projesi)}"
: "${FIRESTORE_BACKUP_URI:?FIRESTORE_BACKUP_URI gerekli}"

if [[ "${ALLOW_RESTORE_DRILL:-false}" != "true" ]]; then
  echo "Geri yükleme için ALLOW_RESTORE_DRILL=true açıkça tanımlanmalıdır." >&2
  exit 2
fi
if [[ "$FIRESTORE_BACKUP_URI" != gs://* ]]; then
  echo "FIRESTORE_BACKUP_URI gs:// ile başlamalıdır." >&2
  exit 4
fi

if [[ "${RESTORE_TEST_PROJECT_IS_DISPOSABLE:-false}" != "true" ]]; then
  echo "Hedefin ayrı ve silinebilir test projesi olduğunu RESTORE_TEST_PROJECT_IS_DISPOSABLE=true ile doğrulayın." >&2
  exit 5
fi
command -v gcloud >/dev/null || { echo "gcloud bulunamadı." >&2; exit 5; }
python_bin="${PYTHON_BIN:-python3}"
command -v "$python_bin" >/dev/null || { echo "$python_bin bulunamadı." >&2; exit 5; }
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
database_id="${RESTORE_TEST_DATABASE_ID:-(default)}"
evidence_dir="${BACKUP_EVIDENCE_DIR:-${repo_dir}/outputs/backup-evidence}"
mkdir -p "$evidence_dir"
temporary_manifest=""
backup_manifest="${BACKUP_EVIDENCE_FILE:-}"
if [[ -z "$backup_manifest" ]]; then
  temporary_manifest="$(mktemp)"
  backup_manifest="$temporary_manifest"
  trap '[[ -n "$temporary_manifest" ]] && rm -f "$temporary_manifest"' EXIT
  gcloud storage cp "${FIRESTORE_BACKUP_URI%/}/backup-evidence.json" "$backup_manifest" >/dev/null
fi

read_evidence() {
  "$python_bin" "$repo_dir/scripts/backup_restore_evidence.py" read --file "$backup_manifest" --field "$1"
}
source_project="$(read_evidence source.projectId)"
source_uri="$(read_evidence backup.uri)"
backup_completed_at="$(read_evidence backup.completedAt)"
verify_document="$(read_evidence verification.documentPath)"
expected_fingerprint="$(read_evidence verification.sha256)"
evidence_kind="$(read_evidence kind)"
evidence_status="$(read_evidence status)"
if [[ "$evidence_kind" != "firestore-backup-evidence" || "$evidence_status" != "passed" ]]; then
  echo "Yedek kanıt dosyası geçerli ve başarılı bir export kaydı değil." >&2
  exit 6
fi
if [[ "$source_project" != "$FIREBASE_PROJECT_ID" ]]; then
  echo "Yedek kanıtındaki kaynak proje beklenen FIREBASE_PROJECT_ID ile eşleşmiyor." >&2
  exit 6
fi
if [[ "$RESTORE_TEST_PROJECT_ID" == "$source_project" || "$RESTORE_TEST_PROJECT_ID" == "$FIREBASE_PROJECT_ID" ]]; then
  echo "Yedeğin kaynak projesi geri yükleme tatbikatı hedefi olamaz." >&2
  exit 3
fi
if [[ "${FIRESTORE_BACKUP_URI%/}" != "${source_uri%/}" ]]; then
  echo "Yedek URI ile kanıt dosyası eşleşmiyor." >&2
  exit 6
fi
if [[ ! "$expected_fingerprint" =~ ^[0-9a-f]{64}$ ]]; then
  echo "Yedek kanıtındaki belge parmak izi geçersiz." >&2
  exit 6
fi

drill_date="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
operation_file="${evidence_dir}/${drill_date}-import-operation.json"
evidence_file="${evidence_dir}/${drill_date}-restore-drill.json"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
started_epoch="$(date -u +%s)"
gcloud firestore import "$FIRESTORE_BACKUP_URI" --project "$RESTORE_TEST_PROJECT_ID" \
  --database "$database_id" --quiet --format=json >"$operation_file"
restored_fingerprint="$($python_bin "$repo_dir/scripts/backup_restore_evidence.py" fingerprint \
  --project "$RESTORE_TEST_PROJECT_ID" --database "$database_id" --document "$verify_document")"
if [[ ! "$restored_fingerprint" =~ ^[0-9a-f]{64}$ || "$restored_fingerprint" != "$expected_fingerprint" ]]; then
  echo "Geri yüklenen doğrulama belgesi kaynak parmak iziyle eşleşmiyor." >&2
  exit 7
fi
completed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
duration_seconds="$(( $(date -u +%s) - started_epoch ))"
rto_args=()
if [[ -n "${RTO_TARGET_SECONDS:-}" ]]; then
  if [[ ! "$RTO_TARGET_SECONDS" =~ ^[1-9][0-9]*$ ]]; then
    echo "RTO_TARGET_SECONDS pozitif tam sayı olmalıdır." >&2
    exit 8
  fi
  rto_args=(--rto-target-seconds "$RTO_TARGET_SECONDS")
fi
"$python_bin" "$repo_dir/scripts/backup_restore_evidence.py" drill \
  --project "$RESTORE_TEST_PROJECT_ID" --database "$database_id" --uri "$FIRESTORE_BACKUP_URI" \
  --backup-completed-at "$backup_completed_at" --started-at "$started_at" --completed-at "$completed_at" \
  --duration-seconds "$duration_seconds" --document "$verify_document" --sha256 "$restored_fingerprint" \
  --output "$evidence_file" "${rto_args[@]}"
if [[ -n "${RTO_TARGET_SECONDS:-}" ]] && (( duration_seconds > RTO_TARGET_SECONDS )); then
  echo "Geri yükleme doğrulandı ancak RTO hedefi aşıldı (${duration_seconds}s > ${RTO_TARGET_SECONDS}s)." >&2
  echo "Kanıt: $evidence_file" >&2
  exit 8
fi
echo "Geri yükleme ve içerik doğrulama tatbikatı tamamlandı: $RESTORE_TEST_PROJECT_ID"
echo "Kanıt: $evidence_file"
echo "Canlı hazırlık için BACKUP_RESTORE_TESTED_AT=$completed_at değerini kaydedin."
echo "Canlı hazırlık için BACKUP_RESTORE_RTO_SECONDS=$duration_seconds değerini kaydedin."
