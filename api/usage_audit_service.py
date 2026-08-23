"""Şirket bazlı, içeriksiz ürün kullanım denetimi.

Finansal değer, dosya adı, kullanıcı mesajı veya analiz sonucu saklanmaz. Kayıt
başarısızlığı ana ürün işlemini engellemez; bu katman yalnız operasyon
görünürlüğü sağlar.
"""

from __future__ import annotations

from typing import Any

from firebase_admin import firestore

from api.auth import _firebase_uygulamasi
from api.models import KimlikBilgisi


IZINLI_META = {"satir_araligi", "ajan_kapsami", "format", "arsivlendi"}


def _satir_araligi(adet: int) -> str:
    if adet <= 1:
        return "1"
    if adet <= 100:
        return "2-100"
    if adet <= 1_000:
        return "101-1000"
    if adet <= 10_000:
        return "1001-10000"
    return "10000+"


def kullanim_olayi_kaydet(
    kullanici: KimlikBilgisi,
    aksiyon: str,
    kaynak: str,
    *,
    satir_sayisi: int | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    if not kullanici.sirket_id or kullanici.roller.get("gelistirici"):
        return
    guvenli_meta = {
        anahtar: deger
        for anahtar, deger in (meta or {}).items()
        if anahtar in IZINLI_META and isinstance(deger, (str, bool, int))
    }
    if satir_sayisi is not None:
        guvenli_meta["satir_araligi"] = _satir_araligi(max(0, int(satir_sayisi)))
    try:
        db = firestore.client(app=_firebase_uygulamasi())
        db.collection("companies").document(str(kullanici.sirket_id)).collection("auditLogs").document().set({
            "action": aksiyon[:80],
            "resource": kaynak[:120],
            "actorId": kullanici.kullanici_id,
            "actorRole": next((rol for rol, aktif in kullanici.roller.items() if aktif), "unknown"),
            "companyId": kullanici.sirket_id,
            "metadata": guvenli_meta,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "containsFinancialData": False,
            "containsMessageBody": False,
            "containsFileName": False,
        })
    except Exception:
        # Gözlem katmanı ürünün finans/AI işlemini hiçbir zaman durdurmamalı.
        return
