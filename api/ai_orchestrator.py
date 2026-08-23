"""KazKaz V1 için güvenli AI seçimi ve CFO yanıt orkestrasyonu.

Finans motoru hesaplamaların tek doğruluk kaynağıdır. Dil modeli yalnızca bu
hesapları açıklar; finansal değer üretmez ve kullanıcı adına aksiyon alamaz.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from gemini_engine import GeminiEngine
from api.ai_guardrails import AIYanitiDogrulamaHatasi, ai_yanitini_dogrula


SAGLAYICILAR = {
    "nvidia": {"anahtar": "NVIDIA_API_KEY", "rol": "birincil"},
    "groq": {"anahtar": "GROQ_API_KEY", "rol": "yedek"},
    "gemini": {"anahtar": "GEMINI_API_KEY", "rol": "yedek"},
}


@dataclass(frozen=True)
class VeriKalitesi:
    seviye: str
    skor: int
    eksikler: List[str]
    uyarilar: List[str]
    ai_kullanilabilir: bool


@dataclass(frozen=True)
class AIUretimSonucu:
    metin: str
    saglayici: str
    model: str
    yedek_kullanildi: bool
    hatalar: List[str]
    dogrulama_durumu: str
    kontrol_edilen_sayi: int
    reddedilen_sayilar: List[str]


def _dolu_anahtar(adi: str) -> bool:
    return bool(os.getenv(adi, "").strip())


def saglayici_sirasi() -> List[str]:
    """Yapılandırılmış sağlayıcı sırasını güvenli varsayılanlarla döndürür."""
    ham = os.getenv("AI_PROVIDER_ORDER", "").strip()
    if not ham:
        eski_ayar = os.getenv("AI_PROVIDER", "").strip().lower()
        ham = f"{eski_ayar},nvidia,groq,gemini" if eski_ayar else "nvidia,groq,gemini"

    sonuc: List[str] = []
    for ad in (parca.strip().lower() for parca in ham.split(",")):
        if ad in SAGLAYICILAR and ad not in sonuc:
            sonuc.append(ad)
    return sonuc or ["nvidia", "groq", "gemini"]


def ai_durumu() -> Dict[str, Any]:
    sira = saglayici_sirasi()
    return {
        "mod": "sirali_yedekleme",
        "politika": "Her istekte yalnızca bir sağlayıcı kullanılır; hata halinde sıradaki denenir.",
        "finans_motoru": "aktif",
        "saglayicilar": [
            {
                "ad": ad,
                "rol": "birincil" if indeks == 0 else "yedek",
                "hazir": _dolu_anahtar(SAGLAYICILAR[ad]["anahtar"]),
            }
            for indeks, ad in enumerate(sira)
        ],
        "aktif_ajanlar": [
            "veri_kalitesi_ajani",
            "finansal_denetim_ajani",
            "ai_anlatim_ajani",
            "insan_onayi_koruyucusu",
        ],
    }


def veri_kalitesini_degerlendir(veri: Any) -> VeriKalitesi:
    eksikler: List[str] = []
    uyarilar: List[str] = []

    if veri.ciro <= 0:
        eksikler.append("ciro")
    if veri.satis_maliyeti == 0 and veri.faaliyet_giderleri == 0:
        eksikler.append("maliyet ve faaliyet gideri kırılımı")
    if veri.nakit == 0 and veri.alacaklar == 0 and veri.stoklar == 0:
        eksikler.append("işletme sermayesi varlıkları")
    if veri.kisa_vadeli_borc == 0 and veri.uzun_vadeli_borc == 0 and veri.borclar == 0:
        uyarilar.append("Borç alanlarının sıfır olması borç bulunmadığı şeklinde kabul edildi.")
    if veri.ozkaynak == 0:
        eksikler.append("özkaynak")
    if abs(veri.net_kar) > veri.ciro and veri.ciro > 0:
        uyarilar.append("Net kâr/zarar mutlak değeri cirodan yüksek; veri doğrulanmalı.")

    muhasebe_alanlari = {
        "faiz gideri": getattr(veri, "faiz_gideri", None),
        "vergi gideri": getattr(veri, "vergi_gideri", None),
        "amortisman": getattr(veri, "amortisman", None),
        "CapEx": getattr(veri, "capex", None),
    }
    eksik_muhasebe = [ad for ad, deger in muhasebe_alanlari.items() if deger is None]
    if eksik_muhasebe:
        uyarilar.append(
            "FAVÖK ve nakit akışı doğrulaması için eksik: " + ", ".join(eksik_muhasebe) + "."
        )

    skor = max(0, 100 - len(eksikler) * 18 - len(uyarilar) * 7)
    if veri.ciro <= 0 or skor < 45:
        seviye = "yetersiz"
    elif skor < 75:
        seviye = "sinirli"
    else:
        seviye = "iyi"
    return VeriKalitesi(
        seviye=seviye,
        skor=skor,
        eksikler=eksikler,
        uyarilar=uyarilar,
        ai_kullanilabilir=seviye != "yetersiz",
    )


def hassas_veriyi_maskele(metin: str) -> str:
    """Soru içindeki yaygın doğrudan tanımlayıcıları sağlayıcıya gitmeden maskeler."""
    sonuc = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[E-POSTA]", metin, flags=re.I)
    sonuc = re.sub(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", "[IBAN]", sonuc, flags=re.I)
    sonuc = re.sub(r"(?<!\d)\d{11}(?!\d)", "[KİMLİK/TELEFON]", sonuc)
    return sonuc


def _guvenli_prompt(
    mesaj: str,
    denetim: Dict[str, Any],
    kalite: VeriKalitesi,
    sirket_profili: Optional[Dict[str, str]] = None,
) -> str:
    metrikler = denetim["metrikler"]
    kurumsal = denetim.get("metrik_kaydi", {})

    def goster(ad: str) -> str:
        sonuc = kurumsal.get(ad, {})
        if sonuc.get("durum") != "hesaplandi":
            return "hesaplanamadı"
        return f"{sonuc['deger']} {sonuc['birim']} (formül: {sonuc['formula_id']}, güven: {sonuc['guven']})"

    tercih = sirket_profili or {}
    tercih_metni = (
        f"Karar önceliği: {tercih.get('ana_hedef', 'belirtilmedi')}; "
        f"beyan edilen zorluk: {tercih.get('ana_zorluk', 'belirtilmedi')}"
    )
    return f"""
Kullanıcı sorusu: {hassas_veriyi_maskele(mesaj)}

KULLANICI BEYANI — YALNIZCA AÇIKLAMA SIRASI İÇİN:
- {tercih_metni}
- Bu alanlar doğrulanmış finansal veri değildir; sayı, skor, eşik veya mali sonuç üretmek için kullanma.

DOĞRULANMIŞ FİNANS MOTORU ÇIKTISI:
- Brüt kâr: {metrikler['brut_kar']}
- FAVÖK: {metrikler['favok'] if metrikler['favok'] is not None else 'hesaplanamadı'}
- Net kâr marjı: %{metrikler['net_kar_marji']}
- Cari oran: {metrikler['cari_oran'] if metrikler['cari_oran'] is not None else 'hesaplanamadı'}
- Borç/özkaynak: {metrikler['borc_ozkaynak_orani'] if metrikler['borc_ozkaynak_orani'] is not None else 'hesaplanamadı'}
- Net işletme sermayesi: {metrikler['net_isletme_sermayesi']}
- Altman Z': {goster('altman_z_prime')}
- DuPont ROE: {goster('dupont_roe')}
- ROIC: {goster('roic')}
- Serbest nakit akışı: {goster('serbest_nakit_akisi')}
- Tam nakit dönüşüm döngüsü: {goster('nakit_donusum_dongusu')}
- Müşteri ciro HHI: {goster('musteri_hhi')}
- Riskler: {'; '.join(denetim['riskler']) or 'Eşik ihlali görülmedi'}
- Kontrollü aksiyonlar: {'; '.join(denetim['aksiyonlar'])}
- Veri kalitesi: {kalite.seviye} ({kalite.skor}/100)
- Veri uyarıları: {'; '.join(kalite.uyarilar + kalite.eksikler) or 'Yok'}

KURALLAR:
1. Yalnızca yukarıdaki doğrulanmış metriklere dayan.
2. Yeni sayı, oran, sektör ortalaması veya tahmin uydurma.
3. Eksik veriyle kesin hüküm verme; hangi verinin gerektiğini açıkça söyle.
4. Muhasebe kaydı, ödeme, kredi, yatırım veya veri silme işlemi başlatma.
5. Öneriyi dayandığı metrikle aynı cümlede ilişkilendir.
6. Türkçe, kısa ve yönetici dostu yanıt ver.
""".strip()


def ai_yaniti_uret(
    mesaj: str,
    denetim: Dict[str, Any],
    kalite: VeriKalitesi,
    sirket_profili: Optional[Dict[str, str]] = None,
) -> AIUretimSonucu:
    """İlk hazır sağlayıcıyı dener; hata halinde sıradaki sağlayıcıya geçer."""
    hatalar: List[str] = []
    prompt = _guvenli_prompt(mesaj, denetim, kalite, sirket_profili)
    hazirlar = [
        ad for ad in saglayici_sirasi() if _dolu_anahtar(SAGLAYICILAR[ad]["anahtar"])
    ]
    son_dogrulama = None

    for indeks, ad in enumerate(hazirlar):
        try:
            motor = GeminiEngine(
                api_key=os.environ[SAGLAYICILAR[ad]["anahtar"]].strip(),
                provider=ad,
            )
            metin = motor.generate(prompt, max_tokens=900).strip()
            if not metin or metin.startswith("⚠️"):
                raise RuntimeError("sağlayıcı geçerli yanıt üretmedi")
            son_dogrulama = ai_yanitini_dogrula(metin, denetim)
            if not son_dogrulama.uygun:
                raise AIYanitiDogrulamaHatasi("AI yanıtında kaynaksız sayısal değer bulundu")
            return AIUretimSonucu(
                metin=metin,
                saglayici=ad,
                model=motor.model_name,
                yedek_kullanildi=indeks > 0,
                hatalar=hatalar,
                dogrulama_durumu="dogrulandi",
                kontrol_edilen_sayi=son_dogrulama.kontrol_edilen_sayi,
                reddedilen_sayilar=[],
            )
        except Exception as exc:  # sağlayıcı hatası kullanıcıya ham olarak gösterilmez
            hatalar.append(f"{ad}:{type(exc).__name__}")

    return AIUretimSonucu(
        metin="",
        saglayici="kuralli_finans_motoru",
        model="yok",
        yedek_kullanildi=False,
        hatalar=hatalar,
        dogrulama_durumu="kuralli_yedek",
        kontrol_edilen_sayi=son_dogrulama.kontrol_edilen_sayi if son_dogrulama else 0,
        reddedilen_sayilar=son_dogrulama.reddedilen_sayilar if son_dogrulama else [],
    )


def metrik_ozeti(denetim: Dict[str, Any]) -> str:
    m = denetim["metrikler"]
    cari = f"{m['cari_oran']:.2f}" if m["cari_oran"] is not None else "hesaplanamadı"
    favok = f"₺{m['favok']:,.0f}" if m["favok"] is not None else "hesaplanamadı"
    ozet = (
        f"- Net kâr marjı: %{m['net_kar_marji']:.1f}\n"
        f"- Cari oran: {cari}\n"
        f"- FAVÖK: {favok}\n"
        f"- Net işletme sermayesi: ₺{m['net_isletme_sermayesi']:,.0f}"
    )
    etiketler = {
        "altman_z_prime": "Altman Z'",
        "dupont_roe": "DuPont ROE",
        "roic": "ROIC",
        "serbest_nakit_akisi": "Serbest nakit akışı",
        "nakit_donusum_dongusu": "Nakit dönüşüm döngüsü",
        "musteri_hhi": "Müşteri ciro HHI",
    }
    ekler = []
    for ad, etiket in etiketler.items():
        sonuc = denetim.get("metrik_kaydi", {}).get(ad, {})
        if sonuc.get("durum") == "hesaplandi":
            ekler.append(f"- {etiket}: {sonuc['deger']:,.2f} {sonuc['birim']}")
    return ozet + ("\n" + "\n".join(ekler) if ekler else "")


def eksik_veri_metni(kalite: VeriKalitesi) -> str:
    parcalar: Iterable[str] = [*kalite.eksikler, *kalite.uyarilar]
    return "\n".join(f"- {madde}" for madde in parcalar) or "- Belirgin eksik görülmedi."
