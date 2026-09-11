import importlib.util
import json
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "backup_restore_evidence.py"
SPEC = importlib.util.spec_from_file_location("backup_restore_evidence", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class Reference:
    path = "companies/company-a"


class GeoPoint:
    latitude = 41.0
    longitude = 29.0


class TestBackupRestoreEvidence(unittest.TestCase):
    def test_parmak_izi_sozluk_sirasindan_bagimsizdir(self):
        first = {"b": 2, "a": {"z": b"secret", "ref": Reference(), "geo": GeoPoint()}}
        second = {"a": {"geo": GeoPoint(), "ref": Reference(), "z": b"secret"}, "b": 2}
        self.assertEqual(MODULE.document_fingerprint(first), MODULE.document_fingerprint(second))

    def test_kanit_dosyasi_finansal_belge_icerigi_tasimaz(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "backup.json"
            MODULE._backup(Namespace(
                project="source", database="(default)", uri="gs://bucket/backup",
                metadata_uri="gs://bucket/backup/x.overall_export_metadata",
                started_at="2026-09-11T00:00:00Z", completed_at="2026-09-11T00:01:00Z",
                duration_seconds=60, document="system/backup-canary",
                sha256="a" * 64, output=str(output),
            ))
            text = output.read_text(encoding="utf-8")
            self.assertNotIn("secret", text)
            self.assertEqual(json.loads(text)["verification"]["sha256"], "a" * 64)

    def test_tatbikat_rto_ve_yedek_yasini_olcer(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "drill.json"
            MODULE._drill(Namespace(
                project="restore", database="(default)", uri="gs://bucket/backup",
                backup_completed_at="2026-09-10T23:00:00Z",
                started_at="2026-09-11T00:00:00Z", completed_at="2026-09-11T00:02:00Z",
                duration_seconds=120, document="system/backup-canary", sha256="b" * 64,
                rto_target_seconds=180, output=str(output),
            ))
            measurement = json.loads(output.read_text(encoding="utf-8"))["measurement"]
            self.assertEqual(measurement["backupAgeAtDrillSeconds"], 3600)
            self.assertTrue(measurement["rtoTargetMet"])
            self.assertEqual(measurement["rpoStatus"], "requires-consecutive-scheduled-backup-evidence")

    def test_tarih_ve_bayt_normalizasyonu_ham_deger_sizdirmaz(self):
        normalized = MODULE._normalize({
            "at": datetime(2026, 9, 11, tzinfo=timezone.utc),
            "payload": b"customer-financial-data",
        })
        self.assertEqual(normalized["at"], "2026-09-11T00:00:00+00:00")
        self.assertNotIn("customer-financial-data", json.dumps(normalized))

    def test_ardisik_yedek_araligi_rpo_hedefiyle_karsilastirilir(self):
        with TemporaryDirectory() as directory:
            previous = Path(directory) / "previous.json"
            current = Path(directory) / "current.json"
            output = Path(directory) / "cadence.json"
            previous.write_text(json.dumps({"backup": {"completedAt": "2026-09-10T00:00:00Z"}}))
            current.write_text(json.dumps({"backup": {"completedAt": "2026-09-10T23:30:00Z"}}))
            result = MODULE._cadence(Namespace(
                previous=str(previous), current=str(current), target_hours=24, output=str(output),
            ))
            measurement = json.loads(output.read_text(encoding="utf-8"))["measurement"]
            self.assertEqual(result, 0)
            self.assertEqual(measurement["observedIntervalHours"], 23.5)
            self.assertTrue(measurement["rpoTargetMet"])

    def test_rpo_hedefi_asilirsa_basarisiz_kanit_yazilir(self):
        with TemporaryDirectory() as directory:
            previous = Path(directory) / "previous.json"
            current = Path(directory) / "current.json"
            output = Path(directory) / "cadence.json"
            previous.write_text(json.dumps({"backup": {"completedAt": "2026-09-10T00:00:00Z"}}))
            current.write_text(json.dumps({"backup": {"completedAt": "2026-09-11T06:00:00Z"}}))
            result = MODULE._cadence(Namespace(
                previous=str(previous), current=str(current), target_hours=24, output=str(output),
            ))
            evidence = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result, 9)
            self.assertEqual(evidence["status"], "failed")
            self.assertFalse(evidence["measurement"]["rpoTargetMet"])


if __name__ == "__main__":
    unittest.main()
