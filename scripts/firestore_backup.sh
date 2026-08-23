#!/usr/bin/env bash
set -euo pipefail

: "${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID gerekli}"
: "${FIRESTORE_BACKUP_BUCKET:?FIRESTORE_BACKUP_BUCKET gerekli}"

backup_date="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
target="gs://${FIRESTORE_BACKUP_BUCKET%/}/kazkaz/${backup_date}"

gcloud firestore export "$target" --project "$FIREBASE_PROJECT_ID" --quiet
echo "Firestore yedeği oluşturuldu: $target"
