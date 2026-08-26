"""Sabit / değişken gider sınıflandırması — tek kaynak.

KazKaz motorlarında (financial, customer, data_importer) tekrarlayan
anahtar kelime listeleri ve maske hesabı bu modülde konsolide edilir.
Kullanıcı kategori adında SABIT_GIDER_KELIMELERI listesinden birini
kullanmışsa satır "sabit gider" sayılır; aksi halde değişken.

Kullanım:

    from expense_classification import sabit_maskesi, SABIT_GIDER_KELIMELERI

    is_sabit = sabit_maskesi(df)                     # varsayılan liste
    is_sabit = sabit_maskesi(df, ekstra=["danışman"]) # şirket özel ek
    is_sabit = sabit_maskesi(df, kelimeler=["kira"])  # tam override

Gerçek sınıflandırma için kullanıcının ``Gider Tipi`` sütununu doldurması
en doğrusu; anahtar kelime yolu yaklaşım olarak kalır. Bu modül sadece
o yaklaşımın tek kaynağıdır.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional, Sequence

import pandas as pd


# Türkiye KOBİ pratiğinde sabit-nitelikli en yaygın kategori kökenleri.
# Küçük harfe düşürülmüş ve accent-sensitive; pattern regex'e alt-string
# olarak katılır ("kira" → "elektrik kirası" da yakalar).
SABIT_GIDER_KELIMELERI: tuple[str, ...] = (
    "kira",
    "maaş",
    "amortisman",
    "sigorta",
    "abonel",  # abonelik, aboneliği, abonelik → -k → -ğ softening'i yakalar
    "aidat",
)


def _pattern(kelimeler: Iterable[str]) -> str:
    """Regex-safe alt-string alternasyonu (küçük harf, boş girdi güvenli).

    Şirket-özel kategori adları regex meta karakterleri içerebilir
    (ör. "C++", "Sabit (ofis)", "%KDV"); her parça re.escape ile literal
    hale getirilir, aksi halde runtime hatası ya da yanlış eşleşme olur.
    """
    # Metin str.lower() sonra aranıyor; parçaları da küçük harfe düşür
    # (kullanıcı "C++" verdi diye "C\+\+" aramak "c++ lisansı"nda kaçmaz).
    parcalar = [re.escape(p.strip().lower()) for p in kelimeler if p and p.strip()]
    if not parcalar:
        return r"(?!x)x"  # hiçbir şey eşleşmez
    return "|".join(parcalar)


def sabit_maskesi(
    df: pd.DataFrame,
    *,
    kelimeler: Optional[Sequence[str]] = None,
    ekstra: Optional[Sequence[str]] = None,
    kategori_sutunu: str = "Kategori",
) -> "pd.Series[bool]":
    """DataFrame satırlarının sabit gider olup olmadığını döndürür.

    - ``kelimeler`` verilirse varsayılan liste yerine kullanılır (tam override).
    - ``ekstra`` verilirse varsayılan listeye eklenir (şirket-özel genişletme).
    - Kategori sütunu yoksa hepsi False döner (değişken varsayılır).
    """
    if kategori_sutunu not in df.columns:
        return pd.Series(False, index=df.index)

    if kelimeler is not None:
        temel = list(kelimeler)
    else:
        temel = list(SABIT_GIDER_KELIMELERI)
        if ekstra:
            temel.extend(ekstra)

    pattern = _pattern(temel)
    return df[kategori_sutunu].astype(str).str.lower().str.contains(pattern, na=False)
