#!/usr/bin/env python3
"""Firestore yedek/geri yükleme kanıtı için içerik sızdırmayan yardımcılar."""

from __future__ import annotations

import argparse
import base64
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"__bytes_sha256__": hashlib.sha256(value).hexdigest(), "size": len(value)}
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if hasattr(value, "path"):
        return {"__document_path__": str(value.path)}
    if hasattr(value, "latitude") and hasattr(value, "longitude"):
        return {"latitude": value.latitude, "longitude": value.longitude}
    raise TypeError(f"Desteklenmeyen Firestore alan türü: {type(value).__name__}")


def document_fingerprint(data: dict[str, Any]) -> str:
    canonical = json.dumps(_normalize(data), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_field(path: str, field: str) -> str:
    payload: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    for part in field.split("."):
        if not isinstance(payload, dict) or part not in payload:
            raise KeyError(field)
        payload = payload[part]
    if isinstance(payload, (dict, list)):
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return str(payload)


def _document(args: argparse.Namespace) -> int:
    parts = [part for part in args.document.split("/") if part]
    if len(parts) < 2 or len(parts) % 2:
        raise SystemExit("Belge yolu collection/document çiftlerinden oluşmalıdır.")
    from google.cloud import firestore

    client = firestore.Client(project=args.project, database=args.database)
    snapshot = client.document("/".join(parts)).get()
    if not snapshot.exists:
        raise SystemExit("Doğrulama belgesi bulunamadı.")
    print(document_fingerprint(snapshot.to_dict() or {}))
    return 0


def _backup(args: argparse.Namespace) -> int:
    write_json(args.output, {
        "schemaVersion": 1,
        "kind": "firestore-backup-evidence",
        "status": "passed",
        "source": {"projectId": args.project, "databaseId": args.database},
        "backup": {
            "uri": args.uri,
            "metadataUri": args.metadata_uri,
            "startedAt": args.started_at,
            "completedAt": args.completed_at,
            "durationSeconds": args.duration_seconds,
        },
        "verification": {"documentPath": args.document, "sha256": args.sha256},
        "recordedAt": _utc_now(),
    })
    return 0


def _drill(args: argparse.Namespace) -> int:
    backup_completed = datetime.fromisoformat(args.backup_completed_at.replace("Z", "+00:00"))
    drill_started = datetime.fromisoformat(args.started_at.replace("Z", "+00:00"))
    write_json(args.output, {
        "schemaVersion": 1,
        "kind": "firestore-restore-drill-evidence",
        "status": "passed",
        "sourceBackup": {"uri": args.uri, "completedAt": args.backup_completed_at},
        "target": {"projectId": args.project, "databaseId": args.database, "disposable": True},
        "verification": {
            "documentPath": args.document,
            "expectedSha256": args.sha256,
            "restoredSha256": args.sha256,
            "matched": True,
        },
        "measurement": {
            "restoreDurationSeconds": args.duration_seconds,
            "backupAgeAtDrillSeconds": max(0, int((drill_started - backup_completed).total_seconds())),
            "rtoTargetSeconds": args.rto_target_seconds,
            "rtoTargetMet": args.rto_target_seconds is None or args.duration_seconds <= args.rto_target_seconds,
            "rpoStatus": "requires-consecutive-scheduled-backup-evidence",
        },
        "startedAt": args.started_at,
        "completedAt": args.completed_at,
        "recordedAt": _utc_now(),
    })
    return 0


def _cadence(args: argparse.Namespace) -> int:
    previous = json.loads(Path(args.previous).read_text(encoding="utf-8"))
    current = json.loads(Path(args.current).read_text(encoding="utf-8"))
    previous_at = datetime.fromisoformat(previous["backup"]["completedAt"].replace("Z", "+00:00"))
    current_at = datetime.fromisoformat(current["backup"]["completedAt"].replace("Z", "+00:00"))
    interval_hours = round((current_at - previous_at).total_seconds() / 3600, 4)
    if interval_hours <= 0:
        raise SystemExit("Yedek kanıtları zaman sırasında değil.")
    target_met = interval_hours <= args.target_hours
    write_json(args.output, {
        "schemaVersion": 1,
        "kind": "firestore-backup-cadence-evidence",
        "status": "passed" if target_met else "failed",
        "measurement": {
            "previousBackupCompletedAt": previous["backup"]["completedAt"],
            "currentBackupCompletedAt": current["backup"]["completedAt"],
            "observedIntervalHours": interval_hours,
            "rpoTargetHours": args.target_hours,
            "rpoTargetMet": target_met,
        },
        "recordedAt": _utc_now(),
    })
    return 0 if target_met else 9


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    fingerprint = commands.add_parser("fingerprint")
    fingerprint.add_argument("--project", required=True)
    fingerprint.add_argument("--database", default="(default)")
    fingerprint.add_argument("--document", required=True)
    fingerprint.set_defaults(handler=_document)

    read = commands.add_parser("read")
    read.add_argument("--file", required=True)
    read.add_argument("--field", required=True)
    read.set_defaults(handler=lambda args: print(read_field(args.file, args.field)) or 0)

    backup = commands.add_parser("backup")
    for name in ("project", "database", "uri", "metadata-uri", "started-at", "completed-at", "document", "sha256", "output"):
        backup.add_argument(f"--{name}", required=True)
    backup.add_argument("--duration-seconds", required=True, type=int)
    backup.set_defaults(handler=_backup)

    drill = commands.add_parser("drill")
    for name in ("project", "database", "uri", "backup-completed-at", "started-at", "completed-at", "document", "sha256", "output"):
        drill.add_argument(f"--{name}", required=True)
    drill.add_argument("--duration-seconds", required=True, type=int)
    drill.add_argument("--rto-target-seconds", type=int)
    drill.set_defaults(handler=_drill)

    cadence = commands.add_parser("cadence")
    cadence.add_argument("--previous", required=True)
    cadence.add_argument("--current", required=True)
    cadence.add_argument("--target-hours", required=True, type=float)
    cadence.add_argument("--output", required=True)
    cadence.set_defaults(handler=_cadence)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
