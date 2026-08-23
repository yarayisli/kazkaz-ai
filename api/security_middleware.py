"""KazKaz API için hafif yerel güvenlik katmanı.

Üretimde ters proxy/WAF sınırlarının yerine geçmez; uygulama katmanında ikinci
bir koruma ve güvenli varsayılan sağlar.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


_istek_pencereleri: Dict[str, Deque[float]] = defaultdict(deque)
_kilit = threading.Lock()


def hiz_limitlerini_sifirla() -> None:
    """Test ve kontrollü yeniden yükleme için süreç içi sayaçları temizler."""
    with _kilit:
        _istek_pencereleri.clear()


def _istek_kimligi(request: Request) -> str:
    """Yalnız güvenli biçimdeki istemci kimliğini kabul eder, aksi halde üretir."""
    aday = request.headers.get("x-request-id", "").strip()
    if 8 <= len(aday) <= 64 and all(karakter.isalnum() or karakter in "-_" for karakter in aday):
        return aday
    return secrets.token_hex(12)


def _pozitif_tamsayi(adi: str, varsayilan: int) -> int:
    try:
        return max(1, int(os.getenv(adi, str(varsayilan))))
    except ValueError:
        return varsayilan


def _kimlik_anahtari(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        ozet = hashlib.sha256(authorization.encode("utf-8")).hexdigest()[:20]
        return f"token:{ozet}"
    istemci = request.client.host if request.client else "bilinmeyen"
    return f"ip:{istemci}"


def _hiz_izni(anahtar: str, limit: int, simdi: float) -> bool:
    pencere_baslangici = simdi - 60
    with _kilit:
        pencere = _istek_pencereleri[anahtar]
        while pencere and pencere[0] <= pencere_baslangici:
            pencere.popleft()
        if len(pencere) >= limit:
            return False
        pencere.append(simdi)
        return True


def _guvenlik_basliklarini_ekle(response: Response, request: Request, istek_kimligi: str) -> Response:
    response.headers["X-Request-ID"] = istek_kimligi
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["X-DNS-Prefetch-Control"] = "off"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; font-src 'self' data:; "
        "connect-src 'self' https://*.googleapis.com https://*.firebaseio.com wss://*.firebaseio.com; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if os.getenv("APP_ENV", "development").lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        response.headers["Cache-Control"] = "no-cache"
    return response


class ApiGuvenlikMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        istek_kimligi = _istek_kimligi(request)
        maksimum_bayt = _pozitif_tamsayi("MAX_REQUEST_BYTES", 5 * 1024 * 1024)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > maksimum_bayt:
                    return _guvenlik_basliklarini_ekle(
                        JSONResponse(
                            status_code=413,
                            content={"detail": f"İstek gövdesi en fazla {maksimum_bayt} bayt olabilir."},
                        ),
                        request,
                        istek_kimligi,
                    )
            except ValueError:
                return _guvenlik_basliklarini_ekle(
                    JSONResponse(status_code=400, content={"detail": "Geçersiz Content-Length başlığı."}),
                    request,
                    istek_kimligi,
                )

        if request.url.path.startswith(("/api/v1/", "/api/public/")):
            dakikalik_limit = _pozitif_tamsayi("API_RATE_LIMIT_PER_MINUTE", 120)
            if not _hiz_izni(_kimlik_anahtari(request), dakikalik_limit, time.monotonic()):
                return _guvenlik_basliklarini_ekle(
                    JSONResponse(
                        status_code=429,
                        content={"detail": "Dakikalık API kullanım sınırı aşıldı. Lütfen kısa süre sonra tekrar deneyin."},
                        headers={"Retry-After": "60"},
                    ),
                    request,
                    istek_kimligi,
                )

        if request.url.path.startswith("/api/v1/cfo/"):
            ai_limit = _pozitif_tamsayi("AI_RATE_LIMIT_PER_MINUTE", 20)
            if not _hiz_izni(f"ai:{_kimlik_anahtari(request)}", ai_limit, time.monotonic()):
                return _guvenlik_basliklarini_ekle(
                    JSONResponse(
                        status_code=429,
                        content={"detail": "AI kullanım sınırı aşıldı. Lütfen kısa süre sonra tekrar deneyin."},
                        headers={"Retry-After": "60"},
                    ),
                    request,
                    istek_kimligi,
                )

        response = await call_next(request)
        return _guvenlik_basliklarini_ekle(response, request, istek_kimligi)
