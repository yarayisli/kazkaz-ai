"""KazKaz AI birleşik V1 FastAPI uygulaması."""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.config import yerel_env_yukle

yerel_env_yukle()

if os.getenv("SENTRY_DSN", "").strip():
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"].strip(),
            send_default_pii=False,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
            environment=os.getenv("APP_ENV", "development"),
        )
    except (ImportError, ValueError):
        # Hazırlık ucu eksik yapılandırmayı görünür kılar; uygulama yine açılır.
        pass

from api.auth import mevcut_kullanici, mevcut_sirket_uyesi, platform_yoneticisi
from api.agent_services import cfo_ajan_analizi
from api.advanced_agents import gelismis_ajan_analizi
from api.models import (
    CfoAjanAnalizIstegi,
    CfoSohbetIstegi,
    FinansalAnalizIstegi,
    FinansalGorunum,
    GelismisAjanIstegi,
    KimlikBilgisi,
    GoogleSheetsIstegi,
    KurSorgusu,
    GeriBildirimIstegi,
    SirketOlusturmaIstegi,
    UyeCikarmaIstegi,
    UyeDavetIstegi,
    UyeRolGuncellemeIstegi,
    PlatformSirketGuncellemeIstegi,
    PlatformSirketEylemIstegi,
    PlatformGeriBildirimDurumIstegi,
    RaporIstegi,
    CalismaAlaniKaydetIstegi,
)
from api.company_service import sirket_olustur
from api.membership_service import daveti_kabul_et, uye_cikar, uye_davet_et, uye_listesi, uye_rolunu_guncelle
from api.report_engine import excel_raporu_olustur, pdf_raporu_olustur
from api.report_archive_service import arsiv_raporu_olustur, arsiv_raporu_sil, rapor_arsivle, rapor_listesi
from api.google_sheets_service import GoogleSheetsHatasi, google_sheet_dogrula, google_sheets_durumu
from api.fx_engine import KurHatasi, tarihsel_kurlari_getir
from api.subscription_service import abonelik_durumu, kamuya_acik_paketler, odeme_hazirlik_durumu, ozellik_kapisi
from api.feedback_service import geri_bildirim_kaydet
from api.erp_service import erp_baglanti_durumu
from api.compliance_readiness import (
    EsgHazirlikIstegi,
    TfrsHazirlikIstegi,
    esg_hazirligini_degerlendir,
    tfrs_hazirligini_degerlendir,
)
from api.readiness import canli_hazirlik_durumu
from api.security_middleware import ApiGuvenlikMiddleware
from api.services import ai_durumu, cfo_yaniti, finansal_denetim, zaman_serisi_analizi
from api.telemetry import operasyonu_olc, performans_ozeti
from api.usage_audit_service import kullanim_olayi_kaydet
from api.excel_import import ALANLAR, DosyaIcerikHatasi, dosya_dogrula, veri_sablonu_olustur

#: sutun_eslemesi'nde kabul edilen kanonik alanlar (dışarıdan gelen değeri sınırlar).
GECERLI_KANONIK_ALANLAR = frozenset(ALANLAR.values())
from api.workspace_service import (
    calisma_alani_disa_aktar,
    calisma_alani_kaydet,
    calisma_alani_sil,
    calisma_alani_yukle,
)
from api.platform_admin_service import (
    platform_geri_bildirim_durumu,
    platform_olaylari,
    platform_sayaclari,
    platform_sirket_detayi,
    platform_sirket_eylemi,
    platform_sirketleri,
    platform_sirketini_guncelle,
)


def _izinli_originler():
    ham = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    return [origin.strip() for origin in ham.split(",") if origin.strip()]


def _izinli_hostlar():
    ham = os.getenv("ALLOWED_HOSTS", "*")
    return [host.strip() for host in ham.split(",") if host.strip()] or ["*"]


uygulama = FastAPI(
    title="KazKaz AI V1 API",
    version="1.0.0",
    docs_url="/api/docs" if os.getenv("APP_ENV", "development") != "production" else None,
    redoc_url=None,
)
uygulama.add_middleware(TrustedHostMiddleware, allowed_hosts=_izinli_hostlar())
if (
    os.getenv("APP_ENV", "development").lower() == "production"
    and os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
):
    uygulama.add_middleware(HTTPSRedirectMiddleware)
uygulama.add_middleware(ApiGuvenlikMiddleware)
uygulama.add_middleware(
    CORSMiddleware,
    allow_origins=_izinli_originler(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-KazKaz-Report-Id", "X-Request-ID"],
)


@uygulama.get("/api/health")
def saglik():
    return {"durum": "ok", "uygulama": "KazKaz AI", "surum": "1.0.0"}


@uygulama.get("/api/readiness")
def canli_hazirlik():
    return canli_hazirlik_durumu()


@uygulama.get("/api/public/performance")
def kamuya_acik_performans():
    """Asgari örneklem oluşmadan hız veya başarı iddiası yayınlamaz."""
    return performans_ozeti(kamuya_acik=True)


@uygulama.get("/api/v1/platform-admin/erisim")
def platform_admin_erisimi(_kullanici: KimlikBilgisi = Depends(platform_yoneticisi)):
    return {"yetkili": True, "kapsam": "platform_operasyon", "finansal_veri_erisimi": False}


@uygulama.get("/api/v1/platform-admin/ozet")
def platform_admin_ozeti(_kullanici: KimlikBilgisi = Depends(platform_yoneticisi)):
    return {
        "sayaclar": platform_sayaclari(),
        "canli_hazirlik": canli_hazirlik_durumu(),
        "ai": ai_durumu(),
        "performans": performans_ozeti(kamuya_acik=False),
        "odeme": odeme_hazirlik_durumu(),
        "erp": erp_baglanti_durumu(),
        "gizlilik": {
            "finansal_veri_gosterilir": False,
            "geri_bildirim_mesaji_gosterilir": False,
            "kapsam": "işletim metadatası ve toplu sayaçlar",
        },
    }


@uygulama.get("/api/v1/platform-admin/sirketler")
def platform_admin_sirketleri(
    limit: int = Query(default=50, ge=1, le=100),
    _kullanici: KimlikBilgisi = Depends(platform_yoneticisi),
):
    return platform_sirketleri(limit)


@uygulama.get("/api/v1/platform-admin/sirket/{sirket_id}")
def platform_admin_sirket_detayi(
    sirket_id: str,
    _kullanici: KimlikBilgisi = Depends(platform_yoneticisi),
):
    if not sirket_id or len(sirket_id) > 128 or not sirket_id.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(status_code=422, detail="Şirket kimliği geçersiz.")
    return platform_sirket_detayi(sirket_id)


@uygulama.get("/api/v1/platform-admin/olaylar")
def platform_admin_olay_listesi(
    limit: int = Query(default=50, ge=1, le=100),
    _kullanici: KimlikBilgisi = Depends(platform_yoneticisi),
):
    return platform_olaylari(limit)


@uygulama.post("/api/v1/platform-admin/sirket-guncelle")
def platform_admin_sirket_guncelle(
    istek: PlatformSirketGuncellemeIstegi,
    kullanici: KimlikBilgisi = Depends(platform_yoneticisi),
):
    return platform_sirketini_guncelle(istek, kullanici)


@uygulama.post("/api/v1/platform-admin/sirket-eylemi")
def platform_admin_sirket_eylemi(
    istek: PlatformSirketEylemIstegi,
    kullanici: KimlikBilgisi = Depends(platform_yoneticisi),
):
    return platform_sirket_eylemi(istek, kullanici)


@uygulama.post("/api/v1/platform-admin/geri-bildirim-durumu")
def platform_admin_geri_bildirim_guncelle(
    istek: PlatformGeriBildirimDurumIstegi,
    kullanici: KimlikBilgisi = Depends(platform_yoneticisi),
):
    return platform_geri_bildirim_durumu(istek, kullanici)


@uygulama.get("/api/public/plans")
def kamuya_acik_planlar():
    """Ödeme hazır değilken fiyat veya iade garantisi yayınlamaz."""
    return kamuya_acik_paketler()


@uygulama.get("/api/v1/oturum")
def oturum(kullanici: KimlikBilgisi = Depends(mevcut_kullanici)):
    return {"kullanici": kullanici}


@uygulama.post("/api/v1/sirket/olustur")
def yeni_sirket_olustur(
    istek: SirketOlusturmaIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_kullanici),
):
    """İlk şirket çalışma alanını oluşturur ve kullanıcıyı admin olarak atar."""
    return sirket_olustur(istek, kullanici)


@uygulama.get("/api/v1/sirket/uyeler")
def sirket_uyeleri(kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return uye_listesi(kullanici)


@uygulama.post("/api/v1/sirket/davet")
def sirket_uyesi_davet_et(
    istek: UyeDavetIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    return uye_davet_et(istek, kullanici)


@uygulama.post("/api/v1/sirket/davet/kabul")
def sirket_davetini_kabul_et(kullanici: KimlikBilgisi = Depends(mevcut_kullanici)):
    return daveti_kabul_et(kullanici)


@uygulama.post("/api/v1/sirket/uye/rol")
def sirket_uyesi_rolu(
    istek: UyeRolGuncellemeIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    return uye_rolunu_guncelle(istek, kullanici)


@uygulama.post("/api/v1/sirket/uye/cikar")
def sirket_uyesi_cikarma(
    istek: UyeCikarmaIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    return uye_cikar(istek, kullanici)


@uygulama.get("/api/v1/ai/durum")
def yapay_zeka_durumu(_kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    """Anahtarları açığa çıkarmadan AI ve ajan hazırlığını gösterir."""
    return ai_durumu()


@uygulama.get("/api/v1/abonelik/durum")
def paket_durumu(kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return abonelik_durumu(kullanici)


@uygulama.get("/api/v1/abonelik/odeme-hazirligi")
def odeme_hazirligi(_kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return odeme_hazirlik_durumu()


@uygulama.get("/api/v1/erp/durum")
def erp_durumu(_kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return erp_baglanti_durumu()


@uygulama.post("/api/v1/uyum/esg-hazirlik")
def esg_hazirligi(
    istek: EsgHazirlikIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    with operasyonu_olc("esg_veri_hazirligi", satir_sayisi=1):
        sonuc = esg_hazirligini_degerlendir(istek)
    kullanim_olayi_kaydet(kullanici, "analysis.esg_readiness", "compliance/esg")
    return sonuc


@uygulama.post("/api/v1/uyum/tfrs-hazirlik")
def tfrs_hazirligi(
    istek: TfrsHazirlikIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    with operasyonu_olc("tfrs_veri_hazirligi", satir_sayisi=1):
        sonuc = tfrs_hazirligini_degerlendir(istek)
    kullanim_olayi_kaydet(kullanici, "analysis.tfrs_readiness", "compliance/tfrs")
    return sonuc


@uygulama.post("/api/v1/geri-bildirim")
def geri_bildirim(
    istek: GeriBildirimIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    return geri_bildirim_kaydet(istek, kullanici)


@uygulama.post("/api/v1/finans/denetim")
def denetim(
    veri: FinansalGorunum,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    with operasyonu_olc("finansal_denetim", satir_sayisi=1):
        sonuc = finansal_denetim(veri)
    kullanim_olayi_kaydet(kullanici, "analysis.financial_audit", "analysis/financial")
    return sonuc


@uygulama.post("/api/v1/finans/zaman-serisi")
def zaman_serisi(
    istek: FinansalAnalizIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    with operasyonu_olc("zaman_serisi", satir_sayisi=len(istek.satirlar)):
        sonuc = zaman_serisi_analizi(istek)
    kullanim_olayi_kaydet(kullanici, "analysis.time_series", "analysis/time-series", satir_sayisi=len(istek.satirlar))
    return sonuc


@uygulama.post("/api/v1/veri/dosya-dogrula")
async def finans_dosyasi_dogrula(
    request: Request,
    dosya_adi: str = Query(min_length=3, max_length=180),
    sutun_eslemesi: Optional[str] = Query(default=None, max_length=4000),
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    """Excel/CSV dosyasını çalıştırmadan doğrular ve V1 veri sözleşmesine çevirir.

    sutun_eslemesi: şirket için kaydedilmiş {normalize_baslik: kanonik_alan}
    eşlemesinin JSON'u. Standart dışı başlıklı dosyalarda kullanıcının bir
    kez yaptığı eşlemeyi taşır; sonraki yüklemelerde sütun tekrar sorulmaz.
    """
    guvenli_ad = Path(dosya_adi).name
    icerik = await request.body()
    kayitli_esleme = None
    if sutun_eslemesi:
        try:
            aday = json.loads(sutun_eslemesi)
            if isinstance(aday, dict):
                # Yalnızca string→string çiftleri; kanonik alan geçerli olmalı.
                kayitli_esleme = {
                    str(k): str(v) for k, v in aday.items()
                    if isinstance(k, str) and v in GECERLI_KANONIK_ALANLAR
                }
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=422, detail="sutun_eslemesi geçerli bir JSON nesnesi değil.")
    with operasyonu_olc("dosya_dogrulama", istek_bayti=len(icerik)) as olcum:
        try:
            sonuc = dosya_dogrula(icerik, guvenli_ad, kayitli_esleme)
            olcum.satir_sayisi = int(sonuc.get("ozet", {}).get("gecerli_satirlar", 0))
        except DosyaIcerikHatasi as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    kullanim_olayi_kaydet(kullanici, "data.file_validated", "data/import", satir_sayisi=olcum.satir_sayisi)
    return sonuc


@uygulama.get("/api/v1/veri/calisma-alani")
def calisma_alani_getir(kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return calisma_alani_yukle(kullanici)


@uygulama.post("/api/v1/veri/calisma-alani/kaydet")
def calisma_alani_kaydi(
    istek: CalismaAlaniKaydetIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    return calisma_alani_kaydet(istek, kullanici)


@uygulama.post("/api/v1/veri/calisma-alani/sil")
def calisma_alani_silme(kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return calisma_alani_sil(kullanici)


@uygulama.get("/api/v1/veri/calisma-alani/disa-aktar")
def calisma_alani_export(kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return Response(
        content=calisma_alani_disa_aktar(kullanici),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="KazKaz_AI_Calisma_Alani.json"'},
    )


@uygulama.get("/api/v1/veri/sablon")
def finans_veri_sablonu(_kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)):
    return Response(
        content=veri_sablonu_olustur(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="KazKaz_AI_V1_Veri_Sablonu.xlsx"'},
    )


@uygulama.get("/api/v1/veri/google-sheets/durum")
def google_sheets_baglanti_durumu(
    _kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    return google_sheets_durumu()


@uygulama.post("/api/v1/veri/google-sheets/dogrula")
def google_sheets_verisi_dogrula(
    istek: GoogleSheetsIstegi,
    _kullanici: KimlikBilgisi = Depends(ozellik_kapisi("google_sheets")),
):
    """Paylaşılan tek bir sayfayı salt-okunur erişimle doğrular."""
    with operasyonu_olc("google_sheets_dogrulama") as olcum:
        try:
            sonuc = google_sheet_dogrula(istek)
            olcum.satir_sayisi = int(sonuc.get("ozet", {}).get("gecerli_satirlar", 0))
            return sonuc
        except (GoogleSheetsHatasi, DosyaIcerikHatasi) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc


@uygulama.post("/api/v1/kur/tarihsel")
def tarihsel_kur_sorgula(
    istek: KurSorgusu,
    _kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    """Tarihsel TCMB döviz alış kurunu kaynak ve efektif tarih kaydıyla döndürür."""
    try:
        return tarihsel_kurlari_getir(istek.tarih, istek.para_birimleri)
    except KurHatasi as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@uygulama.post("/api/v1/rapor/pdf")
def pdf_raporu(
    istek: RaporIstegi,
    kullanici: KimlikBilgisi = Depends(ozellik_kapisi("rapor")),
):
    report_id = rapor_arsivle(istek.finansal_veri, kullanici, "pdf") if istek.arsivle else ""
    return Response(
        content=pdf_raporu_olustur(istek.finansal_veri),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="KazKaz_AI_Yonetici_Raporu.pdf"',
            **({"X-KazKaz-Report-Id": report_id} if report_id else {}),
        },
    )


@uygulama.post("/api/v1/rapor/excel")
def excel_raporu(
    istek: RaporIstegi,
    kullanici: KimlikBilgisi = Depends(ozellik_kapisi("rapor")),
):
    report_id = rapor_arsivle(istek.finansal_veri, kullanici, "excel") if istek.arsivle else ""
    return Response(
        content=excel_raporu_olustur(istek.finansal_veri),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="KazKaz_AI_Yonetici_Raporu.xlsx"',
            **({"X-KazKaz-Report-Id": report_id} if report_id else {}),
        },
    )


@uygulama.get("/api/v1/rapor/arsiv")
def rapor_arsivi(kullanici: KimlikBilgisi = Depends(ozellik_kapisi("rapor"))):
    return rapor_listesi(kullanici)


@uygulama.get("/api/v1/rapor/arsiv/{rapor_id}/{tur}")
def arsiv_raporu_indir(
    rapor_id: str,
    tur: str,
    kullanici: KimlikBilgisi = Depends(ozellik_kapisi("rapor")),
):
    if not rapor_id.startswith("rpt_") or len(rapor_id) > 40:
        raise HTTPException(status_code=422, detail="Rapor kimliği geçersiz.")
    content = arsiv_raporu_olustur(rapor_id, tur, kullanici)
    extension = "pdf" if tur == "pdf" else "xlsx"
    media = "application/pdf" if tur == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return Response(content=content, media_type=media, headers={"Content-Disposition": f'attachment; filename="KazKaz_AI_Arsiv_{rapor_id}.{extension}"'})


@uygulama.post("/api/v1/rapor/arsiv/{rapor_id}/sil")
def arsiv_raporu_silme(
    rapor_id: str,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    return arsiv_raporu_sil(rapor_id, kullanici)


@uygulama.post("/api/v1/cfo/sohbet")
def cfo_sohbet(
    istek: CfoSohbetIstegi,
    kullanici: KimlikBilgisi = Depends(ozellik_kapisi("ai_cfo")),
):
    with operasyonu_olc("ai_cfo_sohbet", satir_sayisi=len(istek.gecmis) + 1):
        sonuc = cfo_yaniti(
            istek.mesaj,
            istek.finansal_veri,
            istek.ajan_denetimi,
            istek.sirket_profili.model_dump() if istek.sirket_profili else None,
        )
    kullanim_olayi_kaydet(kullanici, "ai.cfo_chat", "ai/cfo", meta={"ajan_kapsami": "cfo_chat"})
    return sonuc


@uygulama.post("/api/v1/cfo/ajan-analizi")
def cfo_ajan_araclari(
    istek: CfoAjanAnalizIstegi,
    kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi),
):
    """Eski CFO araçlarını kontrollü V1 veri sözleşmesiyle çalıştırır."""
    with operasyonu_olc(
        "cfo_ajan_analizi",
        satir_sayisi=len(istek.nakit_akisi) + len(istek.borclar) + 1,
    ):
        sonuc = cfo_ajan_analizi(istek)
    kullanim_olayi_kaydet(kullanici, "ai.cfo_agent", "ai/cfo-agent", satir_sayisi=len(istek.nakit_akisi) + len(istek.borclar) + 1)
    return sonuc


@uygulama.post("/api/v1/cfo/gelismis-ajanlar")
def gelismis_cfo_ajanlari(
    istek: GelismisAjanIstegi,
    kullanici: KimlikBilgisi = Depends(ozellik_kapisi("gelismis_ajanlar")),
):
    """Mizan, nakit, alacak, borç, bütçe ve denetim ajanlarını çalıştırır."""
    satir_sayisi = (
        len(istek.mizan)
        + len(istek.haftalik_nakit)
        + len(istek.alacak_faturalari)
        + len(istek.borc_servisi)
        + len(istek.butce)
        + 1
    )
    with operasyonu_olc("gelismis_ajanlar", satir_sayisi=satir_sayisi):
        sonuc = gelismis_ajan_analizi(istek)
    kullanim_olayi_kaydet(kullanici, "ai.advanced_agents", "ai/advanced-agents", satir_sayisi=satir_sayisi, meta={"ajan_kapsami": "7_uzman_ajan"})
    return sonuc


# Tek servisli dağıtımda derlenmiş React uygulamasını aynı origin üzerinden sunar.
_web_dist = Path(__file__).resolve().parents[1] / "web" / "dist"
if _web_dist.exists():
    uygulama.mount("/", StaticFiles(directory=str(_web_dist), html=True), name="web")
