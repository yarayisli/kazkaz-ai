#!/usr/bin/env bash
set -euo pipefail

: "${RESTORE_TEST_PROJECT_ID:?RESTORE_TEST_PROJECT_ID gerekli}"
: "${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID gerekli}"
: "${FIRESTORE_BACKUP_URI:?FIRESTORE_BACKUP_URI gerekli}"

if [[ "${ALLOW_RESTORE_DRILL:-false}" != "true" ]]; then
  echo "Geri yükleme için ALLOW_RESTORE_DRILL=true açıkça tanımlanmalıdır." >&2
  exit 2
fi
if [[ "$RESTORE_TEST_PROJECT_ID" == "$FIREBASE_PROJECT_ID" ]]; then
  echo "Canlı proje geri yükleme tatbikatı hedefi olamaz." >&2
  exit 3
fi
if [[ "$FIRESTORE_BACKUP_URI" != gs://* ]]; then
  echo "FIRESTORE_BACKUP_URI gs:// ile başlamalıdır." >&2
  exit 4
fi

gcloud firestore import "$FIRESTORE_BACKUP_URI" --project "$RESTORE_TEST_PROJECT_ID" --quiet
echo "Geri yükleme tatbikatı tamamlandı: $RESTORE_TEST_PROJECT_ID"
