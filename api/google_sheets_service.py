"""Google Sheets verisini salt-okunur yetkiyle V1 doğrulama motoruna aktarır."""

from __future__ import annotations

import csv
import io
import json
import os
import re
from typing import Any, Callable, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from api.excel_import import DosyaIcerikHatasi, dosya_dogrula
from api.models import GoogleSheetsIstegi


SHEETS_READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
MAKSIMUM_SATIR = 50_001  # Başlık dahil.
MAKSIMUM_SUTUN = 200
_SHEET_ID = re.compile(r"^[A-Za-z0-9_-]{20,}$")


class GoogleSheetsHatasi(ValueError):
    """Kullanıcıya güvenle gösterilebilen bağlantı/okuma hatası."""


def google_sheets_adresini_coz(url: str) -> Tuple[str, Optional[int]]:
    """Yalnızca resmi Google Sheets URL biçimini kabul eder."""
    adres = urlparse(url.strip())
    if adres.scheme != "https" or (adres.hostname or "").lower() != "docs.google.com":
        raise GoogleSheetsHatasi("Yalnızca https://docs.google.com Google Sheets bağlantıları kabul edilir.")
    parcalar = [parca for parca in adres.path.split("/") if parca]
    if len(parcalar) < 3 or parcalar[:2] != ["spreadsheets", "d"]:
        raise GoogleSheetsHatasi("Bağlantı geçerli bir Google Sheets çalışma kitabını göstermiyor.")
    sheet_id = parcalar[2]
    if not _SHEET_ID.fullmatch(sheet_id):
        raise GoogleSheetsHatasi("Google Sheets kimliği geçersiz.")

    sorgu = parse_qs(adres.query)
    fragment = parse_qs(adres.fragment)
    gid_degeri = (sorgu.get("gid") or fragment.get("gid") or [None])[0]
    if gid_degeri is None:
        return sheet_id, None
    if not str(gid_degeri).isdigit():
        raise GoogleSheetsHatasi("Sayfa kimliği (gid) sayısal olmalıdır.")
    return sheet_id, int(gid_degeri)


def _servis_hesabi_bilgisi() -> dict[str, Any]:
    ham = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON", "").strip()
    if not ham:
        raise GoogleSheetsHatasi("Google Sheets bağlantısı sunucuda henüz yapılandırılmamış.")
    try:
        bilgi = json.loads(ham)
    except json.JSONDecodeError as exc:
        raise GoogleSheetsHatasi("Google Sheets servis hesabı yapılandırması geçersiz.") from exc
    if not isinstance(bilgi, dict) or not bilgi.get("client_email") or not bilgi.get("private_key"):
        raise GoogleSheetsHatasi("Google Sheets servis hesabında e-posta veya özel anahtar eksik.")
    return bilgi


def google_sheets_durumu() -> dict[str, Any]:
    """Gizli anahtarı döndürmeden entegrasyon hazırlığını açıklar."""
    try:
        bilgi = _servis_hesabi_bilgisi()
    except GoogleSheetsHatasi:
        return {"yapilandirildi": False, "servis_hesabi_epostasi": None, "yetki": "salt_okunur"}
    return {
        "yapilandirildi": True,
        "servis_hesabi_epostasi": bilgi["client_email"],
        "yetki": "salt_okunur",
    }


def _gspread_istemcisi(bilgi: dict[str, Any]):
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise GoogleSheetsHatasi("Google Sheets sunucu bağımlılıkları kurulu değil.") from exc
    kimlik = Credentials.from_service_account_info(bilgi, scopes=[SHEETS_READONLY_SCOPE])
    return gspread.authorize(kimlik)


def _sayfa_sec(kitap: Any, sayfa_adi: Optional[str], gid: Optional[int]):
    if sayfa_adi:
        return kitap.worksheet(sayfa_adi)
    if gid is not None:
        for sayfa in kitap.worksheets():
            if int(sayfa.id) == gid:
                return sayfa
        raise GoogleSheetsHatasi("Bağlantıdaki sayfa (gid) çalışma kitabında bulunamadı.")
    return kitap.sheet1


def google_sheet_dogrula(
    istek: GoogleSheetsIstegi,
    istemci_uretici: Optional[Callable[[dict[str, Any]], Any]] = None,
) -> dict[str, Any]:
    """Seçili çalışma sayfasını CSV'ye çevirip ortak veri sözleşmesiyle doğrular."""
    sheet_id, gid = google_sheets_adresini_coz(istek.url)
    bilgi = _servis_hesabi_bilgisi()
    try:
        istemci = (istemci_uretici or _gspread_istemcisi)(bilgi)
        kitap = istemci.open_by_key(sheet_id)
        sayfa = _sayfa_sec(kitap, istek.sayfa_adi, gid)
        satirlar = sayfa.get_all_values()
    except GoogleSheetsHatasi:
        raise
    except Exception as exc:
        # Sağlayıcı hatası, belge içeriği veya servis hesabı ayrıntıları sızdırılmaz.
        raise GoogleSheetsHatasi(
            "Google Sheet okunamadı. Belgeyi belirtilen servis hesabıyla Görüntüleyici olarak paylaşın."
        ) from exc

    if not satirlar or not any(any(str(hucre).strip() for hucre in satir) for satir in satirlar):
        raise GoogleSheetsHatasi("Seçilen Google Sheets sayfası boş.")
    if len(satirlar) > MAKSIMUM_SATIR:
        raise GoogleSheetsHatasi("Google Sheets sayfası 50.000 veri satırı sınırını aşıyor.")
    if max((len(satir) for satir in satirlar), default=0) > MAKSIMUM_SUTUN:
        raise GoogleSheetsHatasi("Google Sheets sayfası 200 sütun sınırını aşıyor.")

    tampon = io.StringIO(newline="")
    csv.writer(tampon).writerows(satirlar)
    icerik = tampon.getvalue().encode("utf-8-sig")
    try:
        return dosya_dogrula(icerik, f"Google-Sheets-{sayfa.title}.csv")
    except DosyaIcerikHatasi:
        raise
