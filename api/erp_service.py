"""ERP bağlayıcı sözleşmesi ve Logo için güvenli salt-okunur temel istemci."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests


class ErpYapilandirmaHatasi(RuntimeError):
    pass


class ErpBaglantiHatasi(RuntimeError):
    pass


def _https_adresi(adi: str) -> str:
    deger = os.getenv(adi, "").strip().rstrip("/")
    if not deger:
        raise ErpYapilandirmaHatasi(f"{adi} tanımlı değil")
    parsed = urlparse(deger)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ErpYapilandirmaHatasi(f"{adi} kullanıcı bilgisi içermeyen geçerli bir HTTPS adresi olmalı")
    return deger


def _logo_kontrolleri() -> dict:
    return {
        "api_base_url": bool(os.getenv("LOGO_API_BASE_URL", "").strip()),
        "token_url": bool(os.getenv("LOGO_TOKEN_URL", "").strip()),
        "client_id": bool(os.getenv("LOGO_CLIENT_ID", "").strip()),
        "client_secret": bool(os.getenv("LOGO_CLIENT_SECRET", "").strip()),
        "firma_kodu": bool(os.getenv("LOGO_COMPANY_CODE", "").strip()),
        "salt_okunur_kapsam": bool(os.getenv("LOGO_READONLY_SCOPE", "").strip()),
    }


def erp_baglanti_durumu() -> dict:
    """Anahtarları ve şirket kodlarını açığa çıkarmadan bağlayıcı hazırlığını döndürür."""
    logo = _logo_kontrolleri()
    saglayicilar = {
        "logo": {
            "durum": "yapilandirildi" if all(logo.values()) else "yapilandirilmadi",
            "kontroller": logo,
            "yetki": "salt_okunur",
            "veri_sozlesmesi": ["mizan", "cari_hesap", "fatura", "tahsilat", "banka_hareketi"],
        },
        "mikro": {"durum": "yol_haritasi", "yetki": "salt_okunur"},
        "netsis": {"durum": "yol_haritasi", "yetki": "salt_okunur"},
    }
    return {"durum": "hazir" if saglayicilar["logo"]["durum"] == "yapilandirildi" else "eksik", "saglayicilar": saglayicilar}


@dataclass
class LogoSaltOkunurBaglayici:
    api_base_url: str
    token_url: str
    client_id: str
    client_secret: str
    scope: str
    timeout_seconds: int = 20

    @classmethod
    def ortamdan(cls) -> "LogoSaltOkunurBaglayici":
        if not all(_logo_kontrolleri().values()):
            raise ErpYapilandirmaHatasi("Logo salt-okunur bağlantı ayarları tamamlanmadı")
        try:
            timeout = max(3, min(60, int(os.getenv("LOGO_TIMEOUT_SECONDS", "20"))))
        except ValueError:
            timeout = 20
        return cls(
            api_base_url=_https_adresi("LOGO_API_BASE_URL"),
            token_url=_https_adresi("LOGO_TOKEN_URL"),
            client_id=os.environ["LOGO_CLIENT_ID"].strip(),
            client_secret=os.environ["LOGO_CLIENT_SECRET"].strip(),
            scope=os.environ["LOGO_READONLY_SCOPE"].strip(),
            timeout_seconds=timeout,
        )

    def _token(self) -> str:
        grant_type = os.getenv("LOGO_OAUTH_GRANT_TYPE", "client_credentials").strip()
        if grant_type not in {"client_credentials", "password"}:
            raise ErpYapilandirmaHatasi("Desteklenmeyen Logo OAuth grant türü")
        veri = {"grant_type": grant_type, "scope": self.scope}
        if grant_type == "password":
            kullanici_adi = os.getenv("LOGO_USERNAME", "").strip()
            parola = os.getenv("LOGO_PASSWORD", "").strip()
            if not kullanici_adi or not parola:
                raise ErpYapilandirmaHatasi("Logo password grant için kullanıcı adı ve parola gerekli")
            veri.update({"username": kullanici_adi, "password": parola})
        try:
            yanit = requests.post(
                self.token_url,
                data=veri,
                auth=(self.client_id, self.client_secret),
                timeout=self.timeout_seconds,
            )
            yanit.raise_for_status()
            token = str(yanit.json().get("access_token", "")).strip()
        except (requests.RequestException, ValueError, TypeError) as exc:
            raise ErpBaglantiHatasi("Logo yetkilendirmesi doğrulanamadı") from exc
        if not token:
            raise ErpBaglantiHatasi("Logo token yanıtında access_token bulunamadı")
        return token

    def salt_okunur_get(self, yol: str, *, parametreler: dict | None = None) -> dict | list:
        """Yalnız yapılandırılmış Logo origin'i içinde GET isteği yapar."""
        temiz_yol = yol.strip().lstrip("/")
        if not temiz_yol or ".." in temiz_yol or "//" in temiz_yol:
            raise ErpYapilandirmaHatasi("Logo API yolu geçersiz")
        adres = urljoin(f"{self.api_base_url}/", temiz_yol)
        if urlparse(adres).netloc != urlparse(self.api_base_url).netloc:
            raise ErpYapilandirmaHatasi("Logo isteği yapılandırılmış origin dışına çıkamaz")
        try:
            yanit = requests.get(
                adres,
                params={**(parametreler or {}), "company": os.environ["LOGO_COMPANY_CODE"].strip()},
                headers={"Authorization": f"Bearer {self._token()}", "Accept": "application/json"},
                timeout=self.timeout_seconds,
            )
            yanit.raise_for_status()
            veri = yanit.json()
        except (requests.RequestException, ValueError) as exc:
            raise ErpBaglantiHatasi("Logo salt-okunur veri isteği başarısız") from exc
        if not isinstance(veri, (dict, list)):
            raise ErpBaglantiHatasi("Logo yanıt biçimi desteklenmiyor")
        return veri
