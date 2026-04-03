"""
KazKaz AI - Firebase Auth & Kullanıcı Yönetimi
================================================
Özellikler:
  - Kullanıcı kaydı / girişi (Firebase Auth REST API)
  - Firestore'da kullanıcı profili & paket takibi
  - Paket kontrolü (Free / Pro / Uzman)
  - Oturum yönetimi (Streamlit session)

Kurulum: pip install firebase-admin requests
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum


# ─────────────────────────────────────────────
# PAKET TANIMLAMALARI
# ─────────────────────────────────────────────

class Plan(str, Enum):
    FREE   = "free"
    PRO    = "pro"
    UZMAN  = "uzman"


PLAN_FEATURES: Dict[str, Dict[str, Any]] = {
    Plan.FREE: {
        "ad":              "Free",
        "emoji":           "🆓",
        "fiyat":           "Ücretsiz",
        "temel_analiz":    True,
        "grafikler":       True,
        "saglik_skoru":    True,
        "ai_yorum":        False,
        "ai_sohbet":       False,
        "senaryo_analiz":  False,
        "tahmin":          False,
        "pdf_rapor":       False,
        "gelismis_analiz": False,
        "max_satir":       500,
        "ai_mesaj_limiti": 0,
    },
    Plan.PRO: {
        "ad":              "Pro",
        "emoji":           "⚡",
        "fiyat":           "₺299 / ay",
        "temel_analiz":    True,
        "grafikler":       True,
        "saglik_skoru":    True,
        "ai_yorum":        True,
        "ai_sohbet":       True,
        "senaryo_analiz":  True,
        "tahmin":          False,
        "pdf_rapor":       False,
        "gelismis_analiz": False,
        "max_satir":       5000,
        "ai_mesaj_limiti": 100,
    },
    Plan.UZMAN: {
        "ad":              "Uzman",
        "emoji":           "🚀",
        "fiyat":           "₺799 / ay",
        "temel_analiz":    True,
        "grafikler":       True,
        "saglik_skoru":    True,
        "ai_yorum":        True,
        "ai_sohbet":       True,
        "senaryo_analiz":  True,
        "tahmin":          True,
        "pdf_rapor":       True,
        "gelismis_analiz": True,
        "max_satir":       50000,
        "ai_mesaj_limiti": 500,
    },
}


# ─────────────────────────────────────────────
# FİREBASE AUTH (REST API)
# ─────────────────────────────────────────────

class FirebaseAuth:
    """
    Firebase Authentication REST API istemcisi.
    Admin SDK gerektirmez — sadece Web API Key yeterli.
    """

    BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts"

    def __init__(self, web_api_key: str):
        self.api_key = web_api_key

    def _post(self, endpoint: str, payload: dict) -> Dict[str, Any]:
        url = f"{self.BASE_URL}:{endpoint}?key={self.api_key}"
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if "error" in data:
            raise ValueError(self._parse_error(data["error"]["message"]))
        return data

    @staticmethod
    def _parse_error(code: str) -> str:
        messages = {
            "EMAIL_EXISTS":             "Bu e-posta zaten kayıtlı.",
            "INVALID_EMAIL":            "Geçersiz e-posta adresi.",
            "WEAK_PASSWORD":            "Şifre en az 6 karakter olmalı.",
            "EMAIL_NOT_FOUND":          "E-posta bulunamadı.",
            "INVALID_PASSWORD":         "Hatalı şifre.",
            "USER_DISABLED":            "Hesap devre dışı.",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Çok fazla deneme. Lütfen bekleyin.",
            "INVALID_LOGIN_CREDENTIALS": "E-posta veya şifre hatalı.",
        }
        for key, msg in messages.items():
            if key in code:
                return msg
        return f"Hata: {code}"

    def register(self, email: str, password: str) -> Dict[str, Any]:
        """Yeni kullanıcı kaydı."""
        return self._post("signUp", {
            "email":             email,
            "password":          password,
            "returnSecureToken": True,
        })

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """E-posta/şifre ile giriş."""
        return self._post("signInWithPassword", {
            "email":             email,
            "password":          password,
            "returnSecureToken": True,
        })

    def send_reset_email(self, email: str) -> bool:
        """Şifre sıfırlama e-postası gönder."""
        try:
            self._post("sendOobCode", {
                "requestType": "PASSWORD_RESET",
                "email":       email,
            })
            return True
        except Exception:
            return False

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """ID token yenile."""
        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"
        resp = requests.post(url, json={
            "grant_type":    "refresh_token",
            "refresh_token": refresh_token,
        }, timeout=10)
        return resp.json()


# ─────────────────────────────────────────────
# FİRESTORE KULLANICI YÖNETİMİ
# ─────────────────────────────────────────────

class FirestoreUserManager:
    """
    Firebase Admin SDK ile Firestore kullanıcı profili yönetimi.
    """

    def __init__(self, credentials_path: str, project_id: str):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError:
            raise ImportError("firebase-admin kurulu değil: pip install firebase-admin")

        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)

        from firebase_admin import firestore as fs
        self.db = fs.client()
        self.collection = "users"

    def create_profile(self, uid: str, email: str, plan: str = Plan.FREE) -> Dict[str, Any]:
        """Yeni kullanıcı profili oluştur."""
        profile = {
            "uid":          uid,
            "email":        email,
            "plan":         plan,
            "created_at":   datetime.utcnow().isoformat(),
            "last_login":   datetime.utcnow().isoformat(),
            "ai_msg_count": 0,
            "ai_msg_reset": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "active":       True,
        }
        self.db.collection(self.collection).document(uid).set(profile)
        return profile

    def get_profile(self, uid: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı profilini getir."""
        doc = self.db.collection(self.collection).document(uid).get()
        return doc.to_dict() if doc.exists else None

    def update_plan(self, uid: str, plan: str) -> bool:
        """Kullanıcı paketini güncelle."""
        try:
            self.db.collection(self.collection).document(uid).update({
                "plan":       plan,
                "updated_at": datetime.utcnow().isoformat(),
            })
            return True
        except Exception:
            return False

    def increment_ai_usage(self, uid: str) -> bool:
        """AI mesaj sayacını artır."""
        try:
            from firebase_admin import firestore as fs
            ref = self.db.collection(self.collection).document(uid)
            ref.update({"ai_msg_count": fs.Increment(1)})
            return True
        except Exception:
            return False

    def update_last_login(self, uid: str):
        try:
            self.db.collection(self.collection).document(uid).update({
                "last_login": datetime.utcnow().isoformat()
            })
        except Exception:
            pass

    # ── Analiz Snapshot ───────────────────────────────────────────────────────

    def save_analysis_snapshot(
        self,
        uid:       str,
        rapor:     Dict[str, Any],
        sirket_adi: str = "Şirketim",
        max_snapshots: int = 5,
    ) -> Optional[str]:
        """
        Son analizi Firestore'a kaydeder.
        Kullanıcı başına max 5 snapshot saklanır (eskiler silinir).

        Returns: snapshot_id veya None (hata durumunda)
        """
        try:
            col = self.db.collection("users").document(uid).collection("snapshots")

            # Güvenli serileştirme: DataFrame ve numpy tipler JSON'a çevrilemiyor
            temiz_rapor = _serialize_rapor(rapor)

            snapshot = {
                "sirket_adi":  sirket_adi,
                "tarih":       datetime.utcnow().isoformat(),
                "ay_sayisi":   rapor.get("gelir", {}).get("ay_sayisi", 0),
                "saglik_skor": rapor.get("saglik_skoru", {}).get("skor", 0),
                "toplam_gelir":rapor.get("gelir", {}).get("toplam_gelir", 0),
                "net_kar":     rapor.get("karlilik", {}).get("toplam_net_kar", 0),
                "rapor":       temiz_rapor,
            }

            # Kaydet
            ref = col.add(snapshot)
            snapshot_id = ref[1].id

            # Limit kontrolü: 5'ten fazlaysa en eskiyi sil
            mevcut = list(col.order_by("tarih", direction="ASCENDING").stream())
            if len(mevcut) > max_snapshots:
                for eski in mevcut[:len(mevcut) - max_snapshots]:
                    eski.reference.delete()

            return snapshot_id

        except Exception:
            return None

    def get_snapshots(self, uid: str, limit: int = 5) -> list:
        """
        Kullanıcının son analizlerini listeler.
        Her kayıt: sirket_adi, tarih, saglik_skor, toplam_gelir, net_kar, id
        """
        try:
            col  = self.db.collection("users").document(uid).collection("snapshots")
            docs = col.order_by("tarih", direction="DESCENDING").limit(limit).stream()
            result = []
            for doc in docs:
                d = doc.to_dict()
                result.append({
                    "id":          doc.id,
                    "sirket_adi":  d.get("sirket_adi", "—"),
                    "tarih":       d.get("tarih", "")[:10],
                    "ay_sayisi":   d.get("ay_sayisi", 0),
                    "saglik_skor": d.get("saglik_skor", 0),
                    "toplam_gelir":d.get("toplam_gelir", 0),
                    "net_kar":     d.get("net_kar", 0),
                })
            return result
        except Exception:
            return []

    def get_snapshot_rapor(self, uid: str, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Belirli bir snapshot'ın tam raporunu getirir."""
        try:
            doc = (self.db.collection("users")
                          .document(uid)
                          .collection("snapshots")
                          .document(snapshot_id)
                          .get())
            if doc.exists:
                return doc.to_dict().get("rapor")
            return None
        except Exception:
            return None

    def delete_snapshot(self, uid: str, snapshot_id: str) -> bool:
        """Snapshot siler."""
        try:
            (self.db.collection("users")
                    .document(uid)
                    .collection("snapshots")
                    .document(snapshot_id)
                    .delete())
            return True
        except Exception:
            return False


# ── Yardımcı: Raporu Firestore-safe formata çevir ─────────────────────────────

def _serialize_rapor(obj, depth: int = 0) -> Any:
    """
    DataFrame, numpy tipleri ve diğer serialize edilemeyen nesneleri
    Firestore'a yazılabilir forma çevirir.
    Maksimum 4 seviye derinlikte çalışır (Firestore limiti).
    """
    import numpy as np
    import pandas as pd

    if depth > 4:
        return str(obj)

    if isinstance(obj, dict):
        return {str(k): _serialize_rapor(v, depth+1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_rapor(i, depth+1) for i in obj]
    if isinstance(obj, pd.DataFrame):
        return obj.head(50).to_dict(orient="records")  # max 50 satır
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, float) and (obj != obj):  # NaN kontrolü
        return None
    return obj


# ─────────────────────────────────────────────
# PAKET KONTROL SERVİSİ
# ─────────────────────────────────────────────

class PlanGuard:
    """
    Özellik erişim kontrolü.

    Kullanım:
        guard = PlanGuard(user_profile)
        if guard.can("ai_yorum"):
            # göster
        else:
            guard.show_upgrade_hint("ai_yorum")
    """

    def __init__(self, user_profile: Dict[str, Any]):
        self.plan    = user_profile.get("plan", Plan.FREE)
        self.profile = user_profile
        self.features = PLAN_FEATURES.get(self.plan, PLAN_FEATURES[Plan.FREE])

    def can(self, feature: str) -> bool:
        """Özelliğe erişim var mı?"""
        return bool(self.features.get(feature, False))

    def ai_limit_ok(self) -> bool:
        """AI mesaj limitini aşmadı mı?"""
        limit = self.features.get("ai_mesaj_limiti", 0)
        if limit == 0:
            return False
        kullanilan = self.profile.get("ai_msg_count", 0)
        # Reset tarihi geçtiyse sayaç sıfırla
        reset_str = self.profile.get("ai_msg_reset", "")
        if reset_str:
            try:
                reset_dt = datetime.fromisoformat(reset_str)
                if datetime.utcnow() > reset_dt:
                    return True  # Yeni dönem
            except Exception:
                pass
        return kullanilan < limit

    def remaining_ai_msgs(self) -> int:
        limit    = self.features.get("ai_mesaj_limiti", 0)
        kullanilan = self.profile.get("ai_msg_count", 0)
        return max(0, limit - kullanilan)

    def max_rows(self) -> int:
        return self.features.get("max_satir", 500)

    def plan_info(self) -> Dict[str, Any]:
        return {
            "plan":    self.plan,
            "ad":      self.features.get("ad", ""),
            "emoji":   self.features.get("emoji", ""),
            "fiyat":   self.features.get("fiyat", ""),
            "features": self.features,
        }

    def upgrade_message(self, feature: str) -> str:
        """Özellik kilitliyse hangi pakette var?"""
        for plan_key in [Plan.PRO, Plan.UZMAN]:
            if PLAN_FEATURES[plan_key].get(feature, False):
                p = PLAN_FEATURES[plan_key]
                return (
                    f"Bu özellik **{p['emoji']} {p['ad']}** paketinde mevcut. "
                    f"({p['fiyat']})"
                )
        return "Bu özellik mevcut paketinizde bulunmuyor."


# ─────────────────────────────────────────────
# OTURUm YÖNETİCİSİ (Streamlit)
# ─────────────────────────────────────────────

class SessionManager:
    """
    Streamlit session_state üzerinden oturum yönetimi.
    Firebase'den bağımsız çalışabilir (mock mod).
    """

    @staticmethod
    def login(user_data: Dict[str, Any], profile: Dict[str, Any]):
        import streamlit as st
        st.session_state["user"]          = user_data
        st.session_state["user_profile"]  = profile
        st.session_state["authenticated"] = True
        st.session_state["plan_guard"]    = PlanGuard(profile)

    @staticmethod
    def logout():
        import streamlit as st
        for key in ["user", "user_profile", "authenticated", "plan_guard",
                    "engine", "rapor", "df", "ai_active", "gemini", "chat_history"]:
            st.session_state.pop(key, None)

    @staticmethod
    def is_authenticated() -> bool:
        import streamlit as st
        return st.session_state.get("authenticated", False)

    @staticmethod
    def get_guard() -> Optional[PlanGuard]:
        import streamlit as st
        return st.session_state.get("plan_guard")

    @staticmethod
    def get_profile() -> Optional[Dict[str, Any]]:
        import streamlit as st
        return st.session_state.get("user_profile")

    @staticmethod
    def save_snapshot(rapor: Dict[str, Any], sirket_adi: str = "Şirketim") -> Optional[str]:
        """
        Giriş yapılmışsa analizi Firestore'a kaydeder.
        Sessizce başarısız olur — kullanıcı deneyimini bozmaz.
        """
        import streamlit as st
        try:
            profile = st.session_state.get("user_profile")
            db_mgr  = st.session_state.get("_firestore_mgr")
            if not profile or not db_mgr:
                return None
            uid = profile.get("uid", "")
            if not uid or uid == "demo":
                return None
            return db_mgr.save_analysis_snapshot(uid, rapor, sirket_adi)
        except Exception:
            return None

    @staticmethod
    def list_snapshots() -> list:
        """Kullanıcının kayıtlı analizlerini listeler."""
        import streamlit as st
        try:
            profile = st.session_state.get("user_profile")
            db_mgr  = st.session_state.get("_firestore_mgr")
            if not profile or not db_mgr:
                return []
            return db_mgr.get_snapshots(profile.get("uid", ""))
        except Exception:
            return []

    @staticmethod
    def load_snapshot(snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Kaydedilmiş bir analizi yükler."""
        import streamlit as st
        try:
            profile = st.session_state.get("user_profile")
            db_mgr  = st.session_state.get("_firestore_mgr")
            if not profile or not db_mgr:
                return None
            return db_mgr.get_snapshot_rapor(profile.get("uid", ""), snapshot_id)
        except Exception:
            return None
