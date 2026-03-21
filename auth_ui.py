"""
KazKaz AI - Auth & Paket Yönetimi Arayüzü
==========================================
Modüller:
  - show_auth_page()   → Giriş / Kayıt ekranı
  - show_plan_page()   → Paket seçim ekranı
  - show_user_badge()  → Sidebar kullanıcı bilgisi
  - plan_gate()        → Özellik kilidi decorator

Bağımlılık: firebase_engine.py
"""

import streamlit as st
from firebase_engine import (
    FirebaseAuth,
    FirestoreUserManager,
    SessionManager,
    PlanGuard,
    PLAN_FEATURES,
    Plan,
)

# ─────────────────────────────────────────────
# CSS (auth sayfasına özel)
# ─────────────────────────────────────────────

AUTH_CSS = """
<style>
.auth-card {
    background: linear-gradient(135deg, #0f1629, #111827);
    border: 1px solid #1e2d4a;
    border-radius: 20px;
    padding: 40px 36px;
    max-width: 420px;
    margin: 0 auto;
}
.auth-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4ff, #0066ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.auth-sub {
    color: #4a6fa5;
    font-size: 0.8rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 28px;
}

/* Plan kartları */
.plan-card {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    transition: border-color 0.2s;
    height: 100%;
}
.plan-card.popular {
    border-color: #0066ff;
    background: linear-gradient(135deg, #111827, #0f1e36);
}
.plan-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8eaf0;
    margin: 8px 0 4px;
}
.plan-price {
    font-size: 1.4rem;
    font-weight: 700;
    color: #60a5fa;
    margin-bottom: 16px;
}
.plan-feature {
    font-size: 0.8rem;
    color: #4a6fa5;
    padding: 4px 0;
    border-bottom: 1px solid #1a2540;
}
.plan-feature.yes { color: #10d994; }
.plan-feature.no  { color: #2a3f6a; text-decoration: line-through; }

/* Kullanıcı badge */
.user-badge {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 12px;
}
.user-email { color: #60a5fa; font-size: 0.8rem; }
.user-plan  { color: #10d994; font-size: 0.75rem; letter-spacing:1px; text-transform:uppercase; }

/* Kilitli özellik */
.locked-feature {
    background: #1a1a2e;
    border: 1px dashed #2a3a5a;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    color: #3a5080;
    font-size: 0.85rem;
}
</style>
"""


# ─────────────────────────────────────────────
# YARDIMCI: Firebase bağlantısı
# ─────────────────────────────────────────────

@st.cache_resource
def get_firebase(web_api_key: str) -> FirebaseAuth:
    return FirebaseAuth(web_api_key)


@st.cache_resource
def get_firestore(cred_path: str, project_id: str) -> FirestoreUserManager:
    return FirestoreUserManager(cred_path, project_id)


# ─────────────────────────────────────────────
# 1. GİRİŞ / KAYIT EKRANI
# ─────────────────────────────────────────────

def show_auth_page(web_api_key: str, firestore_cred: str, project_id: str):
    """
    Tam sayfa auth ekranı.
    Başarılı giriş/kayıtta SessionManager.login() çağırır.
    """
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    # Ortalanmış kart
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
        <div style="text-align:center; padding: 30px 0 10px;">
            <div style="font-family:'Syne',sans-serif; font-size:2.6rem; font-weight:800;
                        background:linear-gradient(135deg,#00d4ff,#0066ff,#7c3aed);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                KazKaz AI
            </div>
            <div style="color:#4a6fa5; font-size:0.75rem; letter-spacing:2.5px;
                        text-transform:uppercase; margin-top:4px; margin-bottom:30px;">
                Finansal Analiz Platformu
            </div>
        </div>""", unsafe_allow_html=True)

        tab_giris, tab_kayit = st.tabs(["🔑 Giriş Yap", "✨ Hesap Oluştur"])

        auth    = get_firebase(web_api_key)
        try:
            db  = get_firestore(firestore_cred, project_id)
        except Exception:
            db  = None  # Firestore opsiyonel

        # ── Giriş ──
        with tab_giris:
            email    = st.text_input("E-posta", key="login_email",
                                     placeholder="ornek@sirket.com")
            password = st.text_input("Şifre", type="password", key="login_pass",
                                     placeholder="••••••••")

            if st.button("Giriş Yap", use_container_width=True, key="btn_login"):
                if not email or not password:
                    st.warning("E-posta ve şifre zorunlu.")
                else:
                    with st.spinner("Doğrulanıyor..."):
                        try:
                            user_data = auth.login(email, password)
                            uid       = user_data["localId"]

                            # Profil getir veya oluştur
                            profile = None
                            if db:
                                profile = db.get_profile(uid)
                                if not profile:
                                    profile = db.create_profile(uid, email)
                                else:
                                    db.update_last_login(uid)

                            if not profile:
                                # Firestore yoksa minimal profil
                                profile = {"uid": uid, "email": email, "plan": Plan.FREE,
                                           "ai_msg_count": 0}

                            SessionManager.login(user_data, profile)
                            st.success("✅ Giriş başarılı!")
                            st.rerun()

                        except ValueError as e:
                            st.error(str(e))

            # Şifre sıfırlama
            with st.expander("Şifremi Unuttum"):
                reset_email = st.text_input("E-posta adresiniz", key="reset_email")
                if st.button("Sıfırlama Linki Gönder", key="btn_reset"):
                    if reset_email:
                        ok = auth.send_reset_email(reset_email)
                        if ok:
                            st.success("📧 Sıfırlama e-postası gönderildi.")
                        else:
                            st.error("E-posta gönderilemedi.")

        # ── Kayıt ──
        with tab_kayit:
            new_email    = st.text_input("E-posta", key="reg_email",
                                         placeholder="ornek@sirket.com")
            new_pass     = st.text_input("Şifre (min. 6 karakter)", type="password",
                                         key="reg_pass", placeholder="••••••••")
            new_pass2    = st.text_input("Şifre Tekrar", type="password",
                                         key="reg_pass2", placeholder="••••••••")
            kvkk         = st.checkbox("Kullanım koşullarını ve gizlilik politikasını kabul ediyorum.")

            if st.button("Hesap Oluştur", use_container_width=True, key="btn_register"):
                if not new_email or not new_pass:
                    st.warning("Tüm alanları doldurun.")
                elif new_pass != new_pass2:
                    st.error("Şifreler eşleşmiyor.")
                elif len(new_pass) < 6:
                    st.error("Şifre en az 6 karakter olmalı.")
                elif not kvkk:
                    st.warning("Koşulları kabul etmeniz gerekiyor.")
                else:
                    with st.spinner("Hesap oluşturuluyor..."):
                        try:
                            user_data = auth.register(new_email, new_pass)
                            uid       = user_data["localId"]

                            profile = {"uid": uid, "email": new_email,
                                       "plan": Plan.FREE, "ai_msg_count": 0}
                            if db:
                                profile = db.create_profile(uid, new_email)

                            SessionManager.login(user_data, profile)
                            st.success("🎉 Hesabınız oluşturuldu!")
                            st.balloons()
                            st.rerun()

                        except ValueError as e:
                            st.error(str(e))


# ─────────────────────────────────────────────
# 2. PAKET SEÇİM EKRANI
# ─────────────────────────────────────────────

def show_plan_page():
    """Paket seçim/yükseltme ekranı."""
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown('<div style="font-family:Syne,sans-serif; font-size:1.6rem; font-weight:800; '
                'color:#e8eaf0; margin-bottom:4px;">Paket Seçin</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#4a6fa5; font-size:0.8rem; margin-bottom:24px;">'
                'İhtiyacınıza uygun paketi seçin.</div>', unsafe_allow_html=True)

    guard    = SessionManager.get_guard()
    mevcut   = guard.plan if guard else Plan.FREE

    col1, col2, col3 = st.columns(3)
    plan_cols = [(col1, Plan.FREE), (col2, Plan.PRO), (col3, Plan.UZMAN)]

    for col, plan_key in plan_cols:
        p = PLAN_FEATURES[plan_key]
        popular_class = "popular" if plan_key == Plan.PRO else ""
        popular_badge = '<div style="color:#0066ff;font-size:0.7rem;margin-bottom:4px;">★ EN POPÜLER</div>' \
                        if plan_key == Plan.PRO else ""
        active_badge  = '<div style="color:#10d994;font-size:0.7rem;margin-top:4px;">✓ Mevcut Paketiniz</div>' \
                        if plan_key == mevcut else ""

        features_html = ""
        feature_labels = {
            "temel_analiz":    "Temel Analiz",
            "grafikler":       "Grafikler",
            "saglik_skoru":    "Sağlık Skoru",
            "ai_yorum":        "AI Yorumları",
            "ai_sohbet":       "AI Sohbet",
            "senaryo_analiz":  "Senaryo Analizi",
            "tahmin":          "Gelecek Tahmini",
            "pdf_rapor":       "PDF Rapor",
            "gelismis_analiz": "Gelişmiş Analiz",
        }
        for fk, flabel in feature_labels.items():
            has = p.get(fk, False)
            cls = "yes" if has else "no"
            ico = "✓" if has else "✗"
            features_html += f'<div class="plan-feature {cls}">{ico} {flabel}</div>'

        with col:
            st.markdown(f"""
            <div class="plan-card {popular_class}">
                {popular_badge}
                <div style="font-size:2rem;">{p['emoji']}</div>
                <div class="plan-name">{p['ad']}</div>
                <div class="plan-price">{p['fiyat']}</div>
                {features_html}
                {active_badge}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            if plan_key != mevcut:
                if st.button(
                    f"{'Yükselt →' if plan_key != Plan.FREE else 'Düşür'} {p['ad']}",
                    key=f"plan_{plan_key}",
                    use_container_width=True
                ):
                    # Gerçek ödeme sistemi entegrasyonu buraya
                    st.info(f"'{p['ad']}' paketi için ödeme sistemi yakında aktif olacak.")


# ─────────────────────────────────────────────
# 3. SİDEBAR KULLANICI BADGE
# ─────────────────────────────────────────────

def show_user_badge():
    """Sidebar'da kullanıcı bilgisi ve çıkış butonu gösterir."""
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    profile = SessionManager.get_profile()
    guard   = SessionManager.get_guard()

    if not profile:
        return

    email    = profile.get("email", "")
    plan_key = profile.get("plan", Plan.FREE)
    p_info   = PLAN_FEATURES.get(plan_key, PLAN_FEATURES[Plan.FREE])

    st.markdown(f"""
    <div class="user-badge">
        <div class="user-email">📧 {email}</div>
        <div class="user-plan">{p_info['emoji']} {p_info['ad']} Plan</div>
    </div>""", unsafe_allow_html=True)

    if guard and plan_key in [Plan.PRO, Plan.UZMAN]:
        kalan = guard.remaining_ai_msgs()
        st.markdown(f"""
        <div style="color:#4a6fa5; font-size:0.72rem; margin-bottom:8px;">
            🤖 AI Mesaj: <span style="color:#60a5fa;">{kalan} kaldı</span>
        </div>""", unsafe_allow_html=True)

    if st.button("🚪 Çıkış Yap", use_container_width=True):
        SessionManager.logout()
        st.rerun()


# ─────────────────────────────────────────────
# 4. ÖZELLİK KİLİDİ
# ─────────────────────────────────────────────

def plan_gate(feature: str, label: str = ""):
    """
    Özellik erişim kontrolü.
    Erişim yoksa kilit mesajı gösterir.

    Kullanım:
        if plan_gate("ai_yorum", "AI Yorumları"):
            # özelliği göster
    """
    guard = SessionManager.get_guard()
    if guard and guard.can(feature):
        return True

    msg = guard.upgrade_message(feature) if guard else "Giriş yapmanız gerekiyor."
    st.markdown(f"""
    <div class="locked-feature">
        🔒 <b>{label or feature}</b><br>
        <span style="font-size:0.78rem;">{msg}</span>
    </div>""", unsafe_allow_html=True)
    return False
