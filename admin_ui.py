"""
KazKaz AI — Admin Dashboard
=============================
Sadece admin listesindeki kullanıcılara açık ürün metrikleri sayfası.

Yetkilendirme: ADMIN_EMAILS listesindeki e-postalar veya
`user_profile.role == "admin"` alanı.

Kullanım (app.py):
    from admin_ui import show_admin_tab, is_admin
    if is_admin():
        # navigasyona ekle
    ...
    if nav_sayfa == "admin":
        show_admin_tab(usage_tracker)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Admin listesi — küçük ekiplerde sabit tut, büyüyünce Firestore'a taşı.
ADMIN_EMAILS = {"kankisioyun@gmail.com"}


def is_admin() -> bool:
    """Oturumdaki kullanıcı admin mi?"""
    try:
        profile = st.session_state.get("user_profile") or {}
        email = (profile.get("email") or "").lower().strip()
        if email in {e.lower() for e in ADMIN_EMAILS}:
            return True
        if profile.get("role") == "admin":
            return True
        return False
    except Exception:
        return False


def show_admin_tab(usage_tracker=None):
    """Admin dashboard sayfası."""
    if not is_admin():
        st.warning("🔒 Bu sayfa yalnızca admin kullanıcılar içindir.")
        return

    st.markdown(
        '<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.5rem;'
        'font-weight:800;background:linear-gradient(135deg,#0EA5E9,#1D4ED8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '🛠️ Admin Dashboard</div>'
        '<div style="color:#64748B;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'Kullanım Metrikleri · Ürün Sinyalleri</div>',
        unsafe_allow_html=True)

    if usage_tracker is None or usage_tracker._db is None:
        st.info(
            "📊 Firestore bağlı değil — metrik toplanamıyor. "
            "Prod'da FIREBASE_CRED_PATH ve FIREBASE_PROJECT_ID secret'larını ekleyin."
        )
        return

    n_days = st.slider("Kaç günlük özet?", min_value=7, max_value=90, value=30, step=1)
    with st.spinner("Firestore'dan çekiliyor..."):
        totals = usage_tracker.totals(n_days=n_days)

    # ── Üst KPI'lar ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Bugünkü DAU", totals["dau_today"])
    with c2:
        st.metric(f"Son {n_days} gün — aktif kullanıcı (toplam gün-kullanıcı)",
                  totals["aktif_toplam"])
    with c3:
        toplam_ai = totals["toplam_events"].get("ai_call", 0)
        st.metric(f"AI çağrısı ({n_days} gün)", toplam_ai)
    with c4:
        toplam_pdf = totals["toplam_events"].get("pdf_download", 0)
        st.metric(f"PDF indirme ({n_days} gün)", toplam_pdf)

    st.markdown("---")

    # ── Günlük DAU trendi ──
    st.subheader("📈 Günlük Aktif Kullanıcı (DAU) trendi")
    seri = totals["gunluk_seri"]
    if seri:
        df_dau = pd.DataFrame([
            {"Tarih": r["date"], "DAU": r["unique_users"]}
            for r in seri
        ])
        fig = go.Figure(go.Scatter(
            x=df_dau["Tarih"], y=df_dau["DAU"],
            mode="lines+markers",
            line=dict(color="#1D4ED8", width=2),
            marker=dict(size=5),
        ))
        fig.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=20, b=40),
            xaxis=dict(gridcolor="#E2E8F0"),
            yaxis=dict(gridcolor="#E2E8F0", rangemode="tozero"),
            paper_bgcolor="white", plot_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Sayfa görünümü sıralaması ──
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🗂️ En çok görüntülenen sayfalar")
        pages = totals["toplam_pages"]
        if pages:
            df_pages = (pd.DataFrame(
                [{"Sayfa": k, "Görünüm": v} for k, v in pages.items()])
                .sort_values("Görünüm", ascending=False)
                .reset_index(drop=True))
            st.dataframe(df_pages, use_container_width=True, hide_index=True)
        else:
            st.caption("Henüz sayfa görüntüleme kaydı yok.")

    with c2:
        st.subheader("💳 Plan dağılımı (etkinlik bazlı)")
        plans = totals["toplam_plans"]
        if plans:
            df_plans = pd.DataFrame(
                [{"Plan": k, "Etkinlik": v} for k, v in plans.items()])
            st.dataframe(df_plans, use_container_width=True, hide_index=True)
        else:
            st.caption("Henüz plan bazlı kayıt yok.")

    st.markdown("---")

    # ── Olay türü dağılımı ──
    st.subheader("🎯 Olay türü toplamı")
    events = totals["toplam_events"]
    if events:
        df_events = (pd.DataFrame(
            [{"Olay": k, "Adet": v} for k, v in events.items()])
            .sort_values("Adet", ascending=False)
            .reset_index(drop=True))
        st.dataframe(df_events, use_container_width=True, hide_index=True)
    else:
        st.caption("Henüz olay kaydı yok.")

    # ── Ham JSON (debug) ──
    with st.expander("🔧 Ham veri (debug)"):
        st.json(totals)
