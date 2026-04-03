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


# ─────────────────────────────────────────────────────────────────────────────
# 2. FİYATLANDIRMA & PAKET SEÇİM EKRANI
# ─────────────────────────────────────────────────────────────────────────────

import streamlit.components.v1 as components

# Paket tanımları — görsel katman için genişletilmiş
_PAKETLER = [
    {
        "key":     "free",
        "ad":      "Free",
        "fiyat":   "Ücretsiz",
        "fiyat_alt": "sonsuza kadar",
        "renk":    "#6B7280",
        "populer": False,
        "ozellikler": [
            ("✓", "Temel gelir/gider analizi"),
            ("✓", "Aylık grafikler"),
            ("✓", "Finansal sağlık skoru"),
            ("✓", "500 satır veri limiti"),
            ("✗", "AI yorumları"),
            ("✗", "AI sohbet"),
            ("✗", "Senaryo analizi"),
            ("✗", "Gelecek tahmini"),
            ("✗", "PDF rapor"),
            ("✗", "Gelişmiş analiz"),
        ],
        "cta": "Mevcut Plan",
        "cta_disabled": True,
        "limit_notu": "500 satır / ay",
    },
    {
        "key":     "pro",
        "ad":      "Pro",
        "fiyat":   "₺499",
        "fiyat_alt": "/ ay · KDV dahil",
        "renk":    "#1B3A6B",
        "populer": True,
        "ozellikler": [
            ("✓", "Her şey Free'de olanlar"),
            ("✓", "50.000 satır veri limiti"),
            ("✓", "AI finansal yorumlar"),
            ("✓", "AI sohbet (aylık 100 mesaj)"),
            ("✓", "Senaryo analizi"),
            ("✓", "Gelecek tahmini (Prophet)"),
            ("✓", "PDF rapor indirme"),
            ("✓", "Gelişmiş analiz modülleri"),
            ("✗", "CFO Agent (5 araçlı)"),
            ("✗", "Sınırsız AI mesaj"),
        ],
        "cta": "Pro'ya Geç →",
        "cta_disabled": False,
        "limit_notu": "50.000 satır / ay",
        "iyzico_link": "",   # TODO: iyzico ödeme linki buraya
    },
    {
        "key":     "uzman",
        "ad":      "Uzman",
        "fiyat":   "₺999",
        "fiyat_alt": "/ ay · KDV dahil",
        "renk":    "#0F2252",
        "populer": False,
        "ozellikler": [
            ("✓", "Her şey Pro'da olanlar"),
            ("✓", "Sınırsız satır"),
            ("✓", "CFO Agent (5 araçlı ajan)"),
            ("✓", "Sınırsız AI mesaj"),
            ("✓", "Öncelikli destek"),
            ("✓", "Erken özellik erişimi"),
            ("✓", "SMMM çoklu müşteri (yakında)"),
            ("✓", "API erişimi (yakında)"),
            ("✓", "White-label (yakında)"),
            ("✓", "Özel onboarding"),
        ],
        "cta": "Uzman'a Geç →",
        "cta_disabled": False,
        "limit_notu": "Sınırsız",
        "iyzico_link": "",   # TODO: iyzico ödeme linki buraya
    },
]

_KARSILASTIRMA = [
    ("Veri limiti",           "500 satır",  "50.000 satır",  "Sınırsız"),
    ("Temel analiz",          "✓",          "✓",             "✓"),
    ("Grafikler",             "✓",          "✓",             "✓"),
    ("Sağlık skoru",          "✓",          "✓",             "✓"),
    ("AI yorum",              "✗",          "✓",             "✓"),
    ("AI sohbet",             "✗",          "100/ay",        "Sınırsız"),
    ("Senaryo analizi",       "✗",          "✓",             "✓"),
    ("Gelecek tahmini",       "✗",          "✓",             "✓"),
    ("PDF rapor",             "✗",          "✓",             "✓"),
    ("CFO Agent",             "✗",          "✗",             "✓"),
    ("SMMM çoklu müşteri",    "✗",          "✗",             "Yakında"),
    ("API erişimi",           "✗",          "✗",             "Yakında"),
]


def show_plan_page():
    """
    Tam fiyatlandırma & paket yükseltme ekranı.
    app.py'de session_state['page'] == 'plans' olduğunda çağrılır.
    """
    guard   = SessionManager.get_guard()
    mevcut  = guard.plan if guard else Plan.FREE

    # ── Başlık ────────────────────────────────────────────────────────────────
    components.html(f"""
    <style>
      * {{ box-sizing:border-box; margin:0; padding:0; }}
      body {{ font-family:-apple-system,'Segoe UI',Arial,sans-serif; background:transparent; }}
    </style>
    <div style="text-align:center; padding:32px 0 8px;">
      <div style="font-size:11px; font-weight:600; letter-spacing:.12em; text-transform:uppercase;
                  color:#6B7280; margin-bottom:10px;">FİYATLANDIRMA</div>
      <div style="font-size:28px; font-weight:700; color:#1A1F36; margin-bottom:8px;">
        Her şirketin bir CFO'ya ihtiyacı var
      </div>
      <div style="font-size:14px; color:#6B7280; max-width:480px; margin:0 auto;">
        Kurumsal düzeyde finansal analiz ve AI karar desteğini KOBİ'lere erişilebilir kılıyoruz.
      </div>
    </div>
    """, height=130)

    # ── 3 Paket Kartı ─────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3, gap="medium")
    paket_cols = [col1, col2, col3]

    for i, (col, paket) in enumerate(zip(paket_cols, _PAKETLER)):
        is_mevcut = (paket["key"] == mevcut)
        is_populer = paket["populer"]

        with col:
            # Popüler badge
            if is_populer:
                st.markdown(
                    '<div style="text-align:center; margin-bottom:-8px;">'
                    '<span style="background:#1B3A6B; color:#fff; font-size:10px; '
                    'font-weight:700; letter-spacing:.1em; text-transform:uppercase; '
                    'padding:4px 14px; border-radius:20px;">⭐ EN POPÜLER</span></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown('<div style="height:22px;"></div>', unsafe_allow_html=True)

            # Kart HTML
            border = f"2px solid {paket['renk']}" if is_populer else "1px solid #E8EAEF"
            ozellik_html = ""
            for ico, metin in paket["ozellikler"]:
                renk = "#059669" if ico == "✓" else "#D1D5DB"
                metin_renk = "#374151" if ico == "✓" else "#9CA3AF"
                ozellik_html += (
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'padding:5px 0;border-bottom:1px solid #F3F4F6;">'
                    f'<span style="color:{renk};font-weight:700;font-size:13px;'
                    f'flex-shrink:0;">{ico}</span>'
                    f'<span style="color:{metin_renk};font-size:13px;">{metin}</span>'
                    f'</div>'
                )

            mevcut_badge = (
                '<div style="background:#ECFDF5;color:#059669;font-size:11px;'
                'font-weight:600;padding:3px 10px;border-radius:20px;'
                'display:inline-block;margin-top:8px;">✓ Mevcut Paketiniz</div>'
                if is_mevcut else ""
            )

            components.html(f"""
            <style>* {{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,'Segoe UI',Arial,sans-serif;}}</style>
            <div style="background:#fff;border:{border};border-radius:16px;
                        padding:24px 20px;min-height:480px;">
              <div style="font-size:22px;font-weight:700;color:#1A1F36;">{paket['ad']}</div>
              <div style="margin:12px 0 4px;">
                <span style="font-size:32px;font-weight:800;color:{paket['renk']};">{paket['fiyat']}</span>
              </div>
              <div style="font-size:12px;color:#9CA3AF;margin-bottom:16px;">{paket['fiyat_alt']}</div>
              <div style="font-size:11px;background:#F9FAFB;color:#6B7280;
                          padding:4px 10px;border-radius:6px;margin-bottom:16px;
                          display:inline-block;">{paket['limit_notu']}</div>
              <div style="margin-top:4px;">{ozellik_html}</div>
              {mevcut_badge}
            </div>
            """, height=520)

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            # CTA butonu
            if is_mevcut:
                st.button(
                    "✓ Mevcut Plan",
                    key=f"plan_btn_{paket['key']}",
                    use_container_width=True,
                    disabled=True,
                )
            elif paket["key"] == "free":
                if st.button("Ücretsiz Kullan", key=f"plan_btn_{paket['key']}",
                             use_container_width=True):
                    st.session_state["page"] = "main"
                    st.rerun()
            else:
                iyzico_link = paket.get("iyzico_link", "")
                if iyzico_link:
                    st.markdown(
                        f'<a href="{iyzico_link}" target="_blank" style="display:block;'
                        f'text-align:center;background:#1B3A6B;color:#fff;font-weight:600;'
                        f'font-size:14px;padding:10px;border-radius:8px;text-decoration:none;'
                        f'margin-top:4px;">{paket["cta"]}</a>',
                        unsafe_allow_html=True
                    )
                else:
                    if st.button(paket["cta"], key=f"plan_btn_{paket['key']}",
                                 use_container_width=True):
                        st.info(
                            f"**{paket['ad']} paketi** için ödeme sistemi çok yakında aktif olacak.\n\n"
                            f"Erken erişim için: **destek@kazkaz.ai**",
                            icon="💳"
                        )

    # ── Karşılaştırma Tablosu ─────────────────────────────────────────────────
    st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)

    tablo_html = """
    <style>
      * {box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,'Segoe UI',Arial,sans-serif;}
      .ct {width:100%;border-collapse:collapse;}
      .ct th {background:#F9FAFB;color:#6B7280;font-size:11px;font-weight:700;
              letter-spacing:.08em;text-transform:uppercase;padding:10px 16px;
              border-bottom:2px solid #E8EAEF;text-align:left;}
      .ct th:not(:first-child) {text-align:center;}
      .ct td {padding:10px 16px;font-size:13px;color:#374151;border-bottom:1px solid #F3F4F6;}
      .ct td:not(:first-child) {text-align:center;font-weight:500;}
      .ct tr:hover td {background:#F9FAFB;}
      .yes {color:#059669;} .no {color:#D1D5DB;}
      .pro-col {background:#EFF6FF;}
    </style>
    <div style="font-size:16px;font-weight:700;color:#1A1F36;margin-bottom:12px;">
      Detaylı Özellik Karşılaştırması
    </div>
    <table class="ct">
      <thead>
        <tr>
          <th>Özellik</th>
          <th>Free</th>
          <th style="background:#EFF6FF;color:#1B3A6B;">Pro</th>
          <th>Uzman</th>
        </tr>
      </thead>
      <tbody>
    """
    for satir in _KARSILASTIRMA:
        ozellik, free_v, pro_v, uzman_v = satir
        def stil(v):
            if v == "✓": return f'<span class="yes">✓</span>'
            if v == "✗": return f'<span class="no">✗</span>'
            return v
        tablo_html += (
            f"<tr><td>{ozellik}</td>"
            f"<td>{stil(free_v)}</td>"
            f'<td class="pro-col">{stil(pro_v)}</td>'
            f"<td>{stil(uzman_v)}</td></tr>"
        )
    tablo_html += "</tbody></table>"

    components.html(tablo_html, height=len(_KARSILASTIRMA) * 42 + 90)

    # ── SSS ───────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    with st.expander("❓ Sık Sorulan Sorular"):
        st.markdown("""
**Kredi kartı bilgimi kaydetmeniz gerekiyor mu?**
Ödeme işlemleri iyzico altyapısı üzerinden güvenle gerçekleştirilir.
KazKaz AI kredi kartı bilgilerinizi saklamaz.

**İstediğim zaman iptal edebilir miyim?**
Evet. Aboneliğinizi istediğiniz zaman, herhangi bir ceza ödemeksizin iptal edebilirsiniz.
İptal ettiğinizde mevcut dönem sonuna kadar erişiminiz devam eder.

**Free'den Pro'ya geçince verilerim korunur mu?**
Evet. Hesabınızdaki tüm analizler ve veriler paket geçişinden etkilenmez.

**Fatura kesiliyor mu?**
Evet. Her ödeme döneminde e-fatura otomatik olarak kayıtlı e-posta adresinize gönderilir.

**SMMM olarak birden fazla müşteri için kullanabilir miyim?**
Uzman paketi için SMMM çoklu müşteri modülü geliştiriliyor. Erken erişim için destek@kazkaz.ai adresine yazın.
        """)

    # ── Geri butonu ───────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    if st.button("← Ana Sayfaya Dön", key="plan_back"):
        st.session_state["page"] = "main"
        st.rerun()

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
