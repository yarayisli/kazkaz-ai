import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api.config import yerel_env_yukle


class TestYerelEnv(unittest.TestCase):
    def test_eksik_degerleri_yukler_boslari_atlar(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = Path(klasor) / ".env"
            yol.write_text("TEST_KAZKAZ_ENV=aktif\nBOS_KAZKAZ_ENV=\n", encoding="utf-8")
            with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
                os.environ.pop("TEST_KAZKAZ_ENV", None)
                os.environ.pop("BOS_KAZKAZ_ENV", None)
                yerel_env_yukle(yol)
                self.assertEqual(os.environ["TEST_KAZKAZ_ENV"], "aktif")
                self.assertNotIn("BOS_KAZKAZ_ENV", os.environ)

    def test_mevcut_degeri_ezmez(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = Path(klasor) / ".env"
            yol.write_text("TEST_KAZKAZ_ENV=dosya\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"APP_ENV": "development", "TEST_KAZKAZ_ENV": "process"},
                clear=False,
            ):
                yerel_env_yukle(yol)
                self.assertEqual(os.environ["TEST_KAZKAZ_ENV"], "process")

    def test_production_dosya_yuklemez(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = Path(klasor) / ".env"
            yol.write_text("TEST_KAZKAZ_PROD=yanlis\n", encoding="utf-8")
            with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
                os.environ.pop("TEST_KAZKAZ_PROD", None)
                yerel_env_yukle(yol)
                self.assertNotIn("TEST_KAZKAZ_PROD", os.environ)


if __name__ == "__main__":
    unittest.main()
