"""
KazKaz AI - Bütçe vs Gerçekleşen Streamlit Modülü
===================================================
app.py entegrasyonu:
    from budget_ui import show_budget_tab
    with tab_butce:
        show_budget_tab(df, rapor)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from budget_engine import BudgetEngine, BudgetPlan, BudgetPeriod

# ─────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────

PT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8899bb", family="DM Sans"),
    xaxis=dict(gridcolor="#1e2d4a", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1e2d4a", showgrid=True, zeroline=False),
    margin=dict(l=10, r=10, t=30, b=10),
)
C_GREEN  = "#10d994"
C_RED    = "#ff4757"
C_BLUE   = "#0066ff"
C_YELLOW = "#fbbf24"
C_CYAN   = "#00d4ff"

def fmt(v):
    if abs(v) >= 1_000_000: return f"{v/1_000_000:.1f}M ₺"
    if abs(v) >= 1_000:     return f"{v/1_000:.0f}K ₺"
    return f"{v:,.0f} ₺"

def kpi(label, value, color="#e8eaf0", delta="", positive=True):
    _pos = bool(positive)
    dc = C_GREEN if _pos else C_RED
    di = "▲" if _pos else "▼"
    dh = f'<div style="font-size:.75rem;color:{dc};margin-top:3px;">{di} {delta}</div>' if delta else ""
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#111827,#1a2540);'
        f'border:1px solid #1e3a5f;border-radius:14px;padding:16px 18px;'
        f'position:relative;overflow:hidden;margin-bottom:8px;">'
        f'<div style="position:absolute;top:0;left:0;right:0;height:3px;'
        f'background:linear-gradient(90deg,#00d4ff,#0066ff);"></div>'
        f'<div style="font-size:.7rem;color:#4a6fa5;letter-spacing:1.5px;'
        f'text-transform:uppercase;margin-bottom:5px;">{label}</div>'
        f'<div style="font-family:Syne,sans-serif;font-size:1.5rem;'
        f'font-weight:700;color:{color};">{value}</div>{dh}</div>',
        unsafe_allow_html=True)

def sec(text):
    st.markdown(
        f'<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;'
        f'color:#e8eaf0;padding:6px 0 10px;border-bottom:1px solid #1e2d4a;'
        f'margin:16px 0 14px;">{text}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# BÜTÇE GİRİŞ FORMU
# ─────────────────────────────────────────────

def show_budget_form(gercek_df: pd.DataFrame) -> BudgetPlan:
    """Aylık bütçe giriş formu."""

    sec("📝 Bütçe Girişi")

    # Mevcut dönemleri al
    donemler = sorted(gercek_df["YilAy"].unique()) if "YilAy" in gercek_df.columns else []

    if not donemler:
        st.warning("Önce sol panelden finansal veri yükleyin.")
        return BudgetPlan()

    # Otomatik bütçe önerisi
    otomatik = BudgetEngine.ornek_butce(gercek_df)
    oto_df   = otomatik.to_dataframe()

    giris_yontemi = st.radio(
        "Bütçe Giriş Yöntemi",
        ["🤖 Otomatik Öneri (Ortalama +%10)",
         "📝 Manuel Giriş",
         "📁 CSV Yükle"],
        horizontal=True, key="butce_giris"
    )

    if "Otomatik" in giris_yontemi:
        st.markdown(
            '<div style="background:#0a1a10;border:1px solid #10d99422;'
            'border-radius:10px;padding:12px 16px;margin-bottom:12px;">'
            '<div style="color:#10d994;font-size:.82rem;">'
            '✅ Ortalama aylık gerçekleşenin %10 üzeri bütçe olarak ayarlandı. '
            'İstersen aşağıdan düzenleyebilirsin.</div></div>',
            unsafe_allow_html=True)
        return otomatik

    elif "Manuel" in giris_yontemi:
        st.markdown(
            '<div style="color:#4a6fa5;font-size:.8rem;margin-bottom:12px;">'
            'Her dönem için gelir ve gider bütçenizi girin.</div>',
            unsafe_allow_html=True)

        plan = BudgetPlan()
        cols = st.columns(3)
        col_labels = ["Dönem", "Bütçe Gelir (₺)", "Bütçe Gider (₺)"]

        for j, lbl in enumerate(col_labels):
            cols[j].markdown(
                f'<div style="color:#4a6fa5;font-size:.75rem;'
                f'text-transform:uppercase;letter-spacing:1px;'
                f'margin-bottom:4px;">{lbl}</div>',
                unsafe_allow_html=True)

        # Otomatik değerleri default olarak kullan
        oto_map = {row["Dönem"]: row for _, row in oto_df.iterrows()}

        for donem in donemler:
            oto_row  = oto_map.get(donem, {})
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("", value=donem, disabled=True,
                              key=f"bd_donem_{donem}", label_visibility="collapsed")
            with c2:
                gelir = st.number_input(
                    "", min_value=0,
                    value=int(oto_row.get("Bütçe Gelir", 0)),
                    step=10_000, key=f"bd_gelir_{donem}",
                    label_visibility="collapsed")
            with c3:
                gider = st.number_input(
                    "", min_value=0,
                    value=int(oto_row.get("Bütçe Gider", 0)),
                    step=10_000, key=f"bd_gider_{donem}",
                    label_visibility="collapsed")

            plan.donemler.append(BudgetPeriod(
                donem=donem, butce_gelir=float(gelir), butce_gider=float(gider)))

        return plan

    else:  # CSV Yükle
        uploaded = st.file_uploader(
            "Bütçe CSV yükle",
            type=["csv","xlsx"],
            key="butce_csv",
            help="Sütunlar: Dönem, Bütçe Gelir, Bütçe Gider"
        )
        if uploaded:
            try:
                df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") \
                     else pd.read_excel(uploaded)
                plan = BudgetPlan.from_dataframe(df)
                st.success(f"✅ {len(plan.donemler)} dönem yüklendi.")
                return plan
            except Exception as e:
                st.error(f"CSV okunamadı: {e}")

        # Örnek format
        with st.expander("📋 Örnek CSV Formatı"):
            ornek = pd.DataFrame({
                "Dönem":       ["2024-01","2024-02","2024-03"],
                "Bütçe Gelir": [150000,  160000,  170000],
                "Bütçe Gider": [80000,   85000,   90000],
            })
            st.dataframe(ornek, hide_index=True)
            st.download_button(
                "⬇ Örnek İndir",
                ornek.to_csv(index=False).encode(),
                "butce_sablon.csv", "text/csv",
            )

        return otomatik  # CSV yüklenemezse otomatik kullan


# ─────────────────────────────────────────────
# ANA SEKME
# ─────────────────────────────────────────────

def show_budget_tab(df: pd.DataFrame, fin_rapor: dict = None):
    """Bütçe vs Gerçekleşen ana sekmesi."""

    st.markdown(
        '<div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#00d4ff,#0066ff);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '🎯 Bütçe vs Gerçekleşen</div>'
        '<div style="color:#4a6fa5;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'Sapma Analizi · Kategori Takibi · Yıl Sonu Tahmini</div>',
        unsafe_allow_html=True)

    # Bütçe girişi
    plan = show_budget_form(df)

    if st.button("📊 Analizi Hesapla", use_container_width=True, key="butce_hesapla"):
        with st.spinner("Bütçe analizi yapılıyor..."):
            try:
                engine = BudgetEngine(df, plan)
                st.session_state["butce_rapor"]  = engine.full_report()
                st.session_state["butce_engine"] = engine
            except Exception as e:
                st.error(f"Hata: {e}")
        st.rerun()

    # İlk açılışta otomatik hesapla
    if "butce_rapor" not in st.session_state:
        with st.spinner("Otomatik bütçe analizi yapılıyor..."):
            try:
                engine = BudgetEngine(df, plan)
                st.session_state["butce_rapor"]  = engine.full_report()
                st.session_state["butce_engine"] = engine
            except Exception as e:
                st.error(f"Hata: {e}")
                return

    rapor = st.session_state["butce_rapor"]
    ozet  = rapor.get("ozet", {})
    proj  = rapor.get("projeksiyon", {})
    kars  = rapor.get("karsilastirma", pd.DataFrame())

    if not ozet:
        st.info("Analiz için yeterli veri yok.")
        return

    st.markdown("---")

    # ── KPI Satırı ──
    perf_renk = {
        "🏆 Hedefi Aştı":  C_GREEN,
        "✅ Hedefe Ulaştı": C_GREEN,
        "🟡 Hedefe Yakın":  C_YELLOW,
        "⚠️ Hedef Altı":   "#f97316",
        "❌ Kritik Sapma":  C_RED,
    }.get(ozet.get("performans",""), C_YELLOW)

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Bütçe Gelir",   fmt(ozet.get("toplam_butce_gelir",0)))
    with c2: kpi("Gerçekleşen",   fmt(ozet.get("toplam_gercek_gelir",0)),
                 delta=fmt(abs(ozet.get("gelir_sapma",0))),
                 positive=ozet.get("gelir_sapma",0)>=0,
                 color=C_GREEN if ozet.get("gelir_sapma",0)>=0 else C_RED)
    with c3: kpi("Başarı Oranı",  f'%{ozet.get("gelir_basari_pct",0)}',
                 color=perf_renk)
    with c4: kpi("Hedef Ay",
                 f'{ozet.get("hedef_ay",0)} / {ozet.get("toplam_ay",0)}',
                 "Gelir hedefine ulaşılan ay")
    with c5: kpi("Performans",    ozet.get("performans","-"),
                 color=perf_renk,
                 positive=ozet.get("gelir_basari_pct",0)>=100)

    # ── Alt Sekmeler ──
    s1, s2, s3, s4 = st.tabs([
        "📊 Karşılaştırma",
        "📈 Sapma Grafikleri",
        "🔮 Yıl Sonu Tahmini",
        "📋 Detay Tablo",
    ])

    # ════════ KARŞILAŞTIRMA ════════
    with s1:
        sec("📊 Bütçe vs Gerçekleşen — Aylık")

        if not kars.empty:
            fig = go.Figure()
            fig.add_bar(x=kars["Dönem"], y=kars["Bütçe Gelir"],
                        name="Bütçe Gelir", marker_color="#1e3a5f", opacity=.9)
            fig.add_bar(x=kars["Dönem"], y=kars["Gercek_Gelir"],
                        name="Gerçekleşen Gelir", marker_color=C_BLUE, opacity=.9)
            fig.add_scatter(
                x=kars["Dönem"], y=kars["Gelir Sapma (₺)"],
                name="Sapma (₺)", yaxis="y2",
                mode="lines+markers",
                line=dict(color=C_CYAN, width=2),
                marker=dict(
                    color=[C_GREEN if v>=0 else C_RED
                           for v in kars["Gelir Sapma (₺)"]],
                    size=8,
                ),
            )
            fig.add_hline(y=0, line_dash="dash",
                          line_color="#4a6fa5", opacity=.4, yref="y2")
            fig.update_layout(
                barmode="group", height=320,
                yaxis2=dict(overlaying="y", side="right",
                            gridcolor="#1e2d4a"),
                legend=dict(orientation="h", y=1.1, x=0),
                **PT,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Net karşılaştırma
        sec("💰 Net Kar — Bütçe vs Gerçekleşen")
        if not kars.empty:
            fig2 = go.Figure()
            fig2.add_scatter(
                x=kars["Dönem"], y=kars["Bütçe Net"],
                name="Bütçe Net", mode="lines+markers",
                line=dict(color="#1e3a5f", width=2, dash="dash"),
                marker=dict(size=6),
            )
            fig2.add_scatter(
                x=kars["Dönem"], y=kars["Gercek_Net"],
                name="Gerçekleşen Net", mode="lines+markers",
                line=dict(color=C_GREEN, width=2.5),
                marker=dict(size=7),
                fill="tonexty",
                fillcolor="rgba(16,217,148,0.07)",
            )
            fig2.update_layout(
                height=250, **PT,
                legend=dict(orientation="h", y=1.1, x=0),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ════════ SAPMA GRAFİKLERİ ════════
    with s2:
        sec("📈 Gelir Sapma Analizi")

        if not kars.empty:
            # Sapma bar chart
            colors_sap = [C_GREEN if v >= 0 else C_RED
                          for v in kars["Gelir Sapma (₺)"]]
            fig = go.Figure(go.Bar(
                x=kars["Dönem"],
                y=kars["Gelir Sapma (₺)"],
                marker_color=colors_sap,
                text=[f'{fmt(v)} (%{pct:+.1f})' for v, pct in
                      zip(kars["Gelir Sapma (₺)"], kars["Gelir Sapma (%)"])],
                textposition="outside",
            ))
            fig.add_hline(y=0, line_dash="dash",
                          line_color="#4a6fa5", opacity=.6)
            fig.update_layout(
                title="Aylık Gelir Sapması (Gerçekleşen - Bütçe)",
                height=280, **PT,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Başarı oranı çizgisi
            sec("📊 Aylık Bütçe Başarı Oranı (%)")
            basari = (kars["Gercek_Gelir"] /
                      kars["Bütçe Gelir"].replace(0, np.nan) * 100).fillna(0)

            fig2 = go.Figure(go.Scatter(
                x=kars["Dönem"], y=basari,
                fill="tozeroy", mode="lines+markers",
                line=dict(color=C_BLUE, width=2.5),
                fillcolor="rgba(0,102,255,0.07)",
                marker=dict(
                    color=[C_GREEN if v>=100 else C_RED for v in basari],
                    size=8,
                ),
            ))
            fig2.add_hline(y=100, line_dash="dash",
                           line_color=C_GREEN, opacity=.6,
                           annotation_text="Hedef %100",
                           annotation_font_color=C_GREEN)
            fig2.update_layout(
                height=230,
                yaxis=dict(ticksuffix="%",
                           gridcolor="#1e2d4a", showgrid=True, zeroline=False),
                **{k:v for k,v in PT.items() if k!="yaxis"},
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ════════ YIL SONU TAHMİNİ ════════
    with s3:
        sec("🔮 Yıl Sonu Projeksiyonu")

        if proj:
            c1,c2,c3 = st.columns(3)
            with c1:
                kpi("Yıl Sonu Gelir Tahmini",
                    fmt(proj.get("yilsonu_gelir",0)),
                    f'Yıllık Bütçe: {fmt(proj.get("yillik_butce",0))}')
            with c2:
                fark = proj.get("butce_fark",0)
                kpi("Bütçeye Göre Fark", fmt(abs(fark)),
                    "Bütçe Üstü" if fark>=0 else "Bütçe Altı",
                    positive=fark>=0,
                    color=C_GREEN if fark>=0 else C_RED)
            with c3:
                yp = proj.get("yillik_basari_pct",0)
                kpi("Yıllık Başarı Tahmini", f'%{yp}',
                    color=C_GREEN if yp>=100 else C_YELLOW if yp>=85 else C_RED,
                    positive=yp>=100)

            st.markdown("---")

            # Waterfall chart
            tamamlanan_ay = proj.get("tamamlanan_ay", 0)
            kalan_ay      = proj.get("kalan_ay", 0)

            if not kars.empty:
                fig = go.Figure(go.Waterfall(
                    name="Projeksiyon",
                    orientation="v",
                    measure=["absolute"] + ["relative"] * (tamamlanan_ay - 1) + ["total"],
                    x=list(kars["Dönem"]) + ["Yıl Sonu Tahmini"],
                    y=list(kars["Gercek_Gelir"]) + [
                        kars["Gercek_Gelir"].mean() * kalan_ay
                    ],
                    connector=dict(line=dict(color=C_BLUE, dash="dot")),
                    increasing=dict(marker=dict(color=C_GREEN)),
                    decreasing=dict(marker=dict(color=C_RED)),
                    totals=dict(marker=dict(color=C_BLUE)),
                ))
                fig.add_hline(
                    y=proj.get("yillik_butce",0),
                    line_dash="dash", line_color=C_YELLOW,
                    annotation_text="Yıllık Bütçe",
                    annotation_font_color=C_YELLOW,
                )
                fig.update_layout(
                    title="Aylık Gelir + Yıl Sonu Tahmini",
                    height=320, **PT,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Özet kutu
            st.markdown(
                f'<div style="background:#0d1520;border:1px solid #1e3a5f;'
                f'border-radius:12px;padding:16px 20px;margin-top:10px;">'
                f'<div style="color:#60a5fa;font-weight:700;margin-bottom:8px;">'
                f'📋 Projeksiyon Özeti</div>'
                f'<div style="color:#8aabcc;font-size:.86rem;line-height:1.8;">'
                f'✅ Tamamlanan: <b style="color:#e8eaf0;">{tamamlanan_ay} ay</b> &nbsp;|&nbsp; '
                f'⏳ Kalan: <b style="color:#e8eaf0;">{kalan_ay} ay</b><br>'
                f'💰 Tahmini Yıl Sonu Gelir: <b style="color:{C_CYAN};">'
                f'{fmt(proj.get("yilsonu_gelir",0))}</b><br>'
                f'🎯 Yıllık Bütçe: <b style="color:#e8eaf0;">'
                f'{fmt(proj.get("yillik_butce",0))}</b><br>'
                f'{"✅" if proj.get("butce_fark",0)>=0 else "❌"} '
                f'Bütçe {"üstü" if proj.get("butce_fark",0)>=0 else "altı"}: '
                f'<b style="color:{C_GREEN if proj.get("butce_fark",0)>=0 else C_RED};">'
                f'{fmt(abs(proj.get("butce_fark",0)))}</b>'
                f'</div></div>',
                unsafe_allow_html=True)

    # ════════ DETAY TABLO ════════
    with s4:
        sec("📋 Aylık Detay Tablosu")

        if not kars.empty:
            # Gösterilecek sütunlar
            show_cols = [
                "Dönem",
                "Bütçe Gelir", "Gercek_Gelir", "Gelir Sapma (₺)", "Gelir Sapma (%)",
                "Bütçe Net",   "Gercek_Net",   "Net Sapma (₺)",
                "Gelir Durumu",
            ]
            show_cols = [c for c in show_cols if c in kars.columns]
            display   = kars[show_cols].copy()

            # Sütun adlarını güzelleştir
            display = display.rename(columns={
                "Gercek_Gelir": "Gerç. Gelir",
                "Gercek_Net":   "Gerç. Net",
            })

            def color_sapma(val):
                if isinstance(val, (int, float)):
                    if val > 0:  return "color:#10d994"
                    if val < 0:  return "color:#ff4757"
                return ""

            st.dataframe(
                display.style
                .applymap(color_sapma,
                          subset=[c for c in display.columns
                                  if "Sapma" in c])
                .format({c: "{:,.0f} ₺" for c in display.columns
                         if "₺" not in c and c not in
                         ["Dönem","Gelir Durumu","Gelir Sapma (%)"]}
                        | {"Gelir Sapma (%)": "{:+.1f}%"}),
                use_container_width=True, hide_index=True,
            )

            # İndir
            st.download_button(
                "⬇ Tabloyu İndir",
                display.to_csv(index=False).encode("utf-8"),
                "butce_karsilastirma.csv", "text/csv",
                use_container_width=True,
            )
