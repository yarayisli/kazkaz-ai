"""Nakit toplamları için ondalık aritmetik; API sınırında sonlu sayıya dönüşüm.

Ara toplamlar yuvarlanmaz. Para çıktısı iki basamakta HALF_EVEN kullanır.
Yerel Decimal bağlamı diğer hesapların hassasiyetini değiştirmez.
"""

import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext


class NakitHesaplamaHatasi(ValueError):
    """Geçersiz veya API sayı aralığına sığmayan nakit hesabı."""


def ondalik(deger):
    try:
        sonuc = deger if isinstance(deger, Decimal) else Decimal(str(int(deger) if isinstance(deger, bool) else deger))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise NakitHesaplamaHatasi("Nakit hesabı yalnız sonlu sayısal tutarlarla yapılabilir.") from exc
    if not sonuc.is_finite():
        raise NakitHesaplamaHatasi("Nakit hesabı yalnız sonlu sayısal tutarlarla yapılabilir.")
    return sonuc


def _hassasiyet(degerler):
    # İptal olan büyük tutarların yanında en küçük ondalık basamağı da koru.
    en_buyuk = max((d.adjusted() for d in degerler), default=0)
    en_kucuk = min((d.as_tuple().exponent for d in degerler), default=0)
    return max(28, en_buyuk - en_kucuk + len(str(len(degerler))) + 4)


def topla(degerler):
    sayilar = [ondalik(d) for d in degerler]
    with localcontext() as baglam:
        baglam.prec = _hassasiyet(sayilar)
        return sum(sayilar, Decimal(0))


def cikar(ilk, ikinci):
    return topla([ilk, ondalik(ikinci).copy_negate()])


def sonlu_sayi(deger):
    try:
        sonuc = float(deger)
    except (ValueError, TypeError, OverflowError) as exc:
        raise NakitHesaplamaHatasi("Nakit hesabının sonucu desteklenen sayı aralığını aşıyor.") from exc
    if not math.isfinite(sonuc):
        raise NakitHesaplamaHatasi("Nakit hesabının sonucu desteklenen sayı aralığını aşıyor.")
    return sonuc


def para(deger, basamak=2):
    sayi = ondalik(deger)
    with localcontext() as baglam:
        baglam.prec = max(_hassasiyet([sayi]), sayi.adjusted() + basamak + 4)
        return sonlu_sayi(sayi.quantize(Decimal(1).scaleb(-basamak), rounding=ROUND_HALF_EVEN))


def bol(pay, payda, basamak=2):
    sayilar = [ondalik(pay), ondalik(payda)]
    with localcontext() as baglam:
        baglam.prec = _hassasiyet(sayilar) + 20
        baglam.rounding = ROUND_HALF_EVEN
        return para(sayilar[0] / sayilar[1], basamak)


def ortalama(degerler):
    sayilar = list(degerler)
    return bol(topla(sayilar), len(sayilar))


def ortalama_ham(degerler):
    sayilar = [ondalik(d) for d in degerler]
    with localcontext() as baglam:
        baglam.prec = _hassasiyet(sayilar) + 20
        baglam.rounding = ROUND_HALF_EVEN
        return topla(sayilar) / len(sayilar)
