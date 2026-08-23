"""Yerel geliştirme ayarlarını güvenli biçimde yükler.

Üretim ortamında platformun verdiği environment değişkenleri tek kaynaktır.
Yerelde ise depo kökündeki ``.env`` dosyası yalnızca eksik değişkenleri tamamlar;
mevcut process değerlerini hiçbir zaman ezmez.
"""

from __future__ import annotations

import os
from pathlib import Path


def yerel_env_yukle(env_dosyasi: Path | None = None) -> None:
    if os.getenv("APP_ENV", "development").lower() == "production":
        return

    yol = env_dosyasi or Path(__file__).resolve().parents[1] / ".env"
    if not yol.exists():
        return

    for ham_satir in yol.read_text(encoding="utf-8").splitlines():
        satir = ham_satir.strip()
        if not satir or satir.startswith("#") or "=" not in satir:
            continue
        anahtar, deger = satir.split("=", 1)
        anahtar = anahtar.strip()
        deger = deger.strip().strip("\"'")
        if not anahtar or not deger:
            continue
        os.environ.setdefault(anahtar, deger)
