"""Kişisel veri toplamayan süreç içi operasyon performans ölçümü.

Bu modül kullanıcı, şirket, dosya adı veya finansal değer saklamaz. Yalnızca
operasyon türü, süre, başarı, HTTP durumu, bayt ve satır sayısı gibi toplu
işletim metriklerini sınırlı bir kayan pencerede tutar. Üretimde kalıcı
gözlemlenebilirlik sağlayıcısına aynı anonim kayıtlar yapılandırılmış log olarak
aktarılabilir.
"""

from __future__ import annotations

import json
import logging
import math
import os
import threading
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Deque, Dict, Iterator, Optional


logger = logging.getLogger("kazkaz.telemetry")


@dataclass
class OperasyonOlcumu:
    operasyon: str
    sure_ms: float
    basarili: bool
    durum_kodu: int
    istek_bayti: Optional[int] = None
    satir_sayisi: Optional[int] = None


@dataclass
class OperasyonBaglami:
    istek_bayti: Optional[int] = None
    satir_sayisi: Optional[int] = None
    durum_kodu: int = 200


_kilit = threading.Lock()
_olcumler: Deque[OperasyonOlcumu] = deque(maxlen=5_000)


def _pozitif_tamsayi(adi: str, varsayilan: int) -> int:
    try:
        return max(1, int(os.getenv(adi, str(varsayilan))))
    except ValueError:
        return varsayilan


def telemetriyi_sifirla() -> None:
    """Testlerde ve kontrollü yerel yeniden başlatmada ölçümleri temizler."""
    with _kilit:
        _olcumler.clear()


def _kaydet(olcum: OperasyonOlcumu) -> None:
    global _olcumler
    hedef_uzunluk = _pozitif_tamsayi("PERFORMANCE_WINDOW_SIZE", 5_000)
    with _kilit:
        if _olcumler.maxlen != hedef_uzunluk:
            _olcumler = deque(_olcumler, maxlen=hedef_uzunluk)
        _olcumler.append(olcum)
    logger.info(
        "operasyon_telemetrisi %s",
        json.dumps(
            {
                "operasyon": olcum.operasyon,
                "sure_ms": round(olcum.sure_ms, 2),
                "basarili": olcum.basarili,
                "durum_kodu": olcum.durum_kodu,
                "istek_bayti": olcum.istek_bayti,
                "satir_sayisi": olcum.satir_sayisi,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )


@contextmanager
def operasyonu_olc(
    operasyon: str,
    *,
    istek_bayti: Optional[int] = None,
    satir_sayisi: Optional[int] = None,
) -> Iterator[OperasyonBaglami]:
    """Bir analiz işlemini sonuç ve istisna durumlarıyla birlikte ölçer."""
    baslangic = perf_counter()
    baglam = OperasyonBaglami(istek_bayti=istek_bayti, satir_sayisi=satir_sayisi)
    basarili = False
    try:
        yield baglam
        basarili = True
    except Exception as exc:
        baglam.durum_kodu = int(getattr(exc, "status_code", 500))
        raise
    finally:
        _kaydet(
            OperasyonOlcumu(
                operasyon=operasyon,
                sure_ms=(perf_counter() - baslangic) * 1_000,
                basarili=basarili,
                durum_kodu=baglam.durum_kodu,
                istek_bayti=baglam.istek_bayti,
                satir_sayisi=baglam.satir_sayisi,
            )
        )


def _yuzdelik(degerler: list[float], oran: float) -> float:
    if not degerler:
        return 0.0
    sirali = sorted(degerler)
    konum = max(0, math.ceil(len(sirali) * oran) - 1)
    return round(sirali[konum], 2)


def _grup_ozeti(olcumler: list[OperasyonOlcumu]) -> Dict[str, object]:
    basarili = [olcum for olcum in olcumler if olcum.basarili]
    sureler = [olcum.sure_ms for olcum in basarili]
    satirlar = [olcum.satir_sayisi for olcum in olcumler if olcum.satir_sayisi is not None]
    baytlar = [olcum.istek_bayti for olcum in olcumler if olcum.istek_bayti is not None]
    return {
        "orneklem": len(olcumler),
        "basari_orani": round((len(basarili) / len(olcumler)) * 100, 2) if olcumler else 0.0,
        "p50_ms": _yuzdelik(sureler, 0.50),
        "p95_ms": _yuzdelik(sureler, 0.95),
        "maksimum_ms": round(max(sureler), 2) if sureler else 0.0,
        "ortalama_satir": round(sum(satirlar) / len(satirlar), 2) if satirlar else None,
        "ortalama_istek_bayti": round(sum(baytlar) / len(baytlar), 2) if baytlar else None,
    }


def performans_ozeti(*, kamuya_acik: bool = False) -> Dict[str, object]:
    """Kayan pencerenin anonim performans özetini döndürür.

    Kamuya açık özet, az örnekle yanıltıcı pazarlama iddiası oluşmaması için
    asgari örneklem eşiğinin altında yüzdelik değer yayınlamaz.
    """
    with _kilit:
        kopya = list(_olcumler)
    asgari_ornek = _pozitif_tamsayi("PUBLIC_PERFORMANCE_MIN_SAMPLES", 30)
    temel = {
        "olusturulma_zamani": datetime.now(timezone.utc).isoformat(),
        "kisisel_veri_toplanir": False,
        "asgari_orneklem": asgari_ornek,
    }
    if kamuya_acik and len(kopya) < asgari_ornek:
        return {
            **temel,
            "durum": "yetersiz_veri",
            "mesaj": "Yayınlanabilir performans aralığı için yeterli üretim örneği henüz oluşmadı.",
        }

    gruplar: Dict[str, list[OperasyonOlcumu]] = defaultdict(list)
    for olcum in kopya:
        gruplar[olcum.operasyon].append(olcum)
    ozet = _grup_ozeti(kopya)
    if kamuya_acik:
        # Ham örnek adedi ve operasyon kırılımı dışarıya verilmez; bunlar sahte
        # sosyal kanıta veya şirket aktivitesi çıkarımına dönüştürülmemelidir.
        return {
            **temel,
            "durum": "yayina_hazir",
            "basari_orani": ozet["basari_orani"],
            "p50_ms": ozet["p50_ms"],
            "p95_ms": ozet["p95_ms"],
            "orneklem": f"{asgari_ornek}+",
        }
    return {
        **temel,
        "durum": "hazir",
        "genel": ozet,
        "operasyonlar": {ad: _grup_ozeti(degerler) for ad, degerler in sorted(gruplar.items())},
    }
