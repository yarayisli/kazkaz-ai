"""
KazKaz AI - Yatırım Analizi Streamlit Modülü
=============================================
app.py'e entegrasyon:
    from investment_ui import show_investment_tab
    # Tab içinde:
    with tab_yatirim:
        show_investment_tab()
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from design_system import *

from typing import List

from investment_engine import Investment, InvestmentEngine, InvestmentComparator

# ─────────────────────────────────────────────
# TEMA SABİTLERİ
# ─────────────────────────────────────────────

def kpi_card(label, value, delta="", color="#0F172A", positive=True):
    dc = "#059669" if positive else "#DC2626"
    di = "▲" if positive else "▼"
    dh = f'<div style="font-size:0.76rem;color:{dc};margin-top:3px;">{di} {delta}</div>' if delta else ""
    st.markdown(f"""
    <div style="background:#FFFFFF;
                border:1px solid #E2E8F0;border-radius:14px;
                padding:16px 18px;position:relative;overflow:hidden;margin-bottom:8px;">
        <div style="position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:4px 0 0 4px;
                    background:linear-gradient(90deg,#0EA5E9,#1D4ED8);"></div>
        <div style="font-size:0.7rem;color:#64748B;letter-spacing:1.5px;
                    text-transform:uppercase;margin-bottom:5px;">{label}</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.55rem;
                    font-weight:700;color:{color};">{value}</div>
        {dh}
    </div>""", unsafe_allow_html=True)

def section_title(text: str):
    st.markdown(f"""
    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;
                color:#0F172A;padding:6px 0 10px;border-bottom:1px solid #E2E8F0;
                margin:16px 0 14px;">{text}</div>""", unsafe_allow_html=True)

def show_investment_tab():
    """Ana yatırım analizi sekmesi — app.py'e entegre edilir."""

    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
                background:linear-gradient(135deg,#0EA5E9,#1D4ED8);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                margin-bottom:4px;">💼 Yatırım Analizi</div>
    <div style="color:#64748B;font-size:0.78rem;letter-spacing:2px;
                text-transform:uppercase;margin-bottom:20px;">
        ROI · NPV · IRR · Payback · Monte Carlo Risk Simülasyonu
    </div>""", unsafe_allow_html=True)

    sub_tab1, sub_tab2, sub_tab3 = st.tabs([
        "📊 Yatırım Analizi",
        "🔀 Karşılaştırma",
        "🎲 Monte Carlo",
    ])

    with sub_tab1:
        _single_investment_ui()

    with sub_tab2:
        _comparison_ui()

    with sub_tab3:
        _monte_carlo_ui()

# ─────────────────────────────────────────────
# TEK YATIRIM ANALİZİ
# ─────────────────────────────────────────────

def _single_investment_ui():
    section_title("📋 Yatırım Parametreleri")

    col1, col2 = st.columns(2)
    with col1:
        inv_adi     = st.text_input("Yatırım Adı", value="Yeni Fabrika", key="inv_ad")
        maliyet     = st.number_input("Başlangıç Maliyeti (₺)", min_value=1000,
                                      value=1_000_000, step=10_000, key="inv_maliyet")
        iskonto     = st.slider("İskonto Oranı / WACC (%)", 1, 50, 12, key="inv_iskonto") / 100
        vergi       = st.slider("Vergi Oranı (%)", 0, 50, 22, key="inv_vergi") / 100

    with col2:
        enflasyon   = st.slider("Enflasyon Oranı (%)", 0, 100, 40, key="inv_enfl") / 100
        yil_sayisi  = st.slider("Analiz Süresi (Yıl)", 1, 20, 5, key="inv_yil")

        st.markdown('<div style="color:#64748B;font-size:0.78rem;margin-bottom:6px;">'
                    'Yıllık Nakit Akışları (₺)</div>', unsafe_allow_html=True)
        nakit_akislari = []
        cols_cf = st.columns(min(yil_sayisi, 5))
        for i in range(yil_sayisi):
            with cols_cf[i % 5]:
                cf = st.number_input(f"Yıl {i+1}", value=int(maliyet * 0.25),
                                     step=10_000, key=f"cf_{i}")
                nakit_akislari.append(float(cf))

    if st.button("📈 Analizi Hesapla", use_container_width=True, key="inv_calc"):
        try:
            inv = Investment(
                ad=inv_adi,
                baslangic_maliyeti=float(maliyet),
                nakit_akislari=nakit_akislari,
                iskonto_orani=iskonto,
                vergi_orani=vergi,
                enflasyon_orani=enflasyon,
            )
            engine = InvestmentEngine(inv)
            rapor  = engine.full_report()
            st.session_state["inv_rapor"]  = rapor
            st.session_state["inv_engine"] = engine
        except Exception as e:
            st.error(f"Hesaplama hatası: {e}")

    if "inv_rapor" not in st.session_state:
        st.info("👆 Yukarıdaki parametreleri doldurup 'Analizi Hesapla' butonuna tıklayın.")
        return

    rapor  = st.session_state.get("inv_rapor", {})
    if not rapor or "ozet" not in rapor:
        st.info("Analiz sonuçları henüz hazır değil.")
        return

    ozet   = rapor["ozet"]
    skor   = rapor["skor"]
    kdf    = rapor["kumulatif_df"]

    st.markdown("---")
    section_title("📊 Temel Metrikler")

    # KPI satırı 1
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi_card("ROI",   f'%{ozet["roi"]}',
                      f'Yıllık: %{ozet["yillik_roi"]}',
                      color=C_GREEN if ozet["roi"]>0 else C_RED,
                      positive=bool(ozet["roi"]>0))
    with c2:
        npv_col = C_GREEN if ozet["npv"]>0 else C_RED
        kpi_card("NPV", fmt(ozet["npv"]), "Net Bugünkü Değer",
                 color=npv_col, positive=bool(ozet["npv"]>0))
    with c3:
        irr_val = ozet.get("irr")
        irr_str = f'%{irr_val}' if irr_val else "Hesaplanamadı"
        irr_ok  = irr_val and irr_val > ozet["iskonto_orani"]*100
        kpi_card("IRR", irr_str, f'Eşik: %{ozet["iskonto_orani"]*100:.0f}',
                 color=C_GREEN if irr_ok else C_RED, positive=bool(irr_ok))
    with c4:
        pb = ozet.get("payback_basit")
        pb_str = f'{pb:.1f} Yıl' if pb else "Geri Ödenmiyor"
        kpi_card("Geri Ödeme", pb_str,
                 "✅ Geri Ödendi" if ozet["geri_odendi"] else "❌ Süre Dışı",
                 color=C_GREEN if ozet["geri_odendi"] else C_RED,
                 positive=bool(ozet["geri_odendi"]))

    # KPI satırı 2
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi_card("PI", str(ozet["pi"]),
                      "PI > 1 → Kabul Edilebilir",
                      color=C_GREEN if ozet["pi"]>1 else C_RED,
                      positive=bool(ozet["pi"]>1))
    with c2: kpi_card("NPV (Reel)", fmt(ozet["npv_reel"]),
                      "Enflasyon Düzeltmeli",
                      color=C_GREEN if ozet["npv_reel"]>0 else C_RED,
                      positive=bool(ozet["npv_reel"]>0))
    with c3: kpi_card("NPV (Vergi Sonrası)", fmt(ozet["npv_vergi_sonrasi"]),
                      f'Vergi: %{ozet.get("vergi_orani",0.22)*100:.0f}',
                      color=C_GREEN if ozet["npv_vergi_sonrasi"]>0 else C_RED,
                      positive=bool(ozet["npv_vergi_sonrasi"]>0))
    with c4:
        renk = score_color(skor["kategori"])
        kpi_card("Yatırım Skoru", f'{skor["skor"]}/100',
                 skor["kategori"], color=renk, positive=bool(skor["skor"]>=50))

    # Tavsiye kutusu
    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid #BFDBFE;border-radius:12px;
                padding:14px 18px;color:#475569;font-size:0.88rem;
                line-height:1.6;margin:12px 0;">
        <span style="color:{renk};font-weight:700;">💡 Tavsiye:</span>
        {skor["tavsiye"]}
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Grafikler
    col1, col2 = st.columns(2)

    with col1:
        section_title("📅 Kümülatif Nakit Akışı")
        colors_bar = [C_GREEN if v >= 0 else C_RED for v in kdf["Kümülatif"]]
        fig = go.Figure()
        fig.add_bar(x=kdf["Yıl"], y=kdf["Nakit Akışı"],
                    name="Nakit Akışı", marker_color=C_BLUE, opacity=0.8)
        fig.add_scatter(x=kdf["Yıl"], y=kdf["Kümülatif"],
                        name="Kümülatif", mode="lines+markers",
                        line=dict(color=C_GREEN, width=2.5),
                        marker=dict(size=7))
        fig.add_hline(y=0, line_dash="dash", line_color=C_RED, opacity=0.6)
        fig.update_layout(title="Nakit Akışı & Kümülatif",
                          height=300, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("legend","xaxis","yaxis")},
                          legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_title("📊 Yatırım Skor Dağılımı")
        alt = skor["alt_skorlar"]
        labels = ["NPV", "ROI", "IRR", "Geri Ödeme", "PI"]
        values = [alt["npv_skoru"], alt["roi_skoru"], alt["irr_skoru"],
                  alt["payback_skoru"], alt["pi_skoru"]]
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(0,102,255,0.15)",
            line=dict(color=C_BLUE, width=2),
            marker=dict(size=6, color=C_CYAN),
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(range=[0,100], gridcolor="#E2E8F0",
                                tickfont=dict(color="#64748B", size=8)),
                angularaxis=dict(gridcolor="#E2E8F0",
                                 tickfont=dict(color="#94A3B8", size=9)),
            ),
            height=300, **PLOTLY_THEME,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Detay tablosu
    section_title("📋 Yıllık Nakit Akışı Tablosu")
    st.dataframe(
        kdf.style.format({
            "Nakit Akışı":    "{:,.0f} ₺",
            "PV Nakit Akışı": "{:,.0f} ₺",
            "Kümülatif":      "{:,.0f} ₺",
        }).map(
            lambda v: "color: #059669" if isinstance(v, (int, float)) and v >= 0
                      else "color: #DC2626" if isinstance(v, (int, float)) and v < 0
                      else "",
            subset=["Kümülatif"]
        ),
        use_container_width=True, hide_index=True
    )

# ─────────────────────────────────────────────
# KARŞILAŞTIRMA MODÜLü
# ─────────────────────────────────────────────

def _comparison_ui():
    section_title("🔀 Çoklu Yatırım Karşılaştırması")

    n = st.slider("Karşılaştırılacak Yatırım Sayısı", 2, 5, 3, key="comp_n")

    investments: List[Investment] = []
    for i in range(n):
        with st.expander(f"💼 Yatırım {i+1}", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                ad      = st.text_input("Ad", value=f"Seçenek {i+1}", key=f"c_ad_{i}")
                maliyet = st.number_input("Maliyet (₺)", min_value=1000,
                                          value=1_000_000, step=50_000, key=f"c_m_{i}")
            with c2:
                yil   = st.slider("Süre (Yıl)", 1, 15, 5, key=f"c_y_{i}")
                iskonto = st.slider("WACC (%)", 1, 50, 12, key=f"c_r_{i}") / 100
            with c3:
                ort_cf = st.number_input("Ort. Yıllık Nakit Akışı (₺)",
                                          min_value=0, value=int(maliyet*0.25),
                                          step=10_000, key=f"c_cf_{i}")
                buyume = st.slider("Yıllık Büyüme (%)", -20, 50, 5, key=f"c_g_{i}") / 100

            # Büyüme oranıyla nakit akışları oluştur
            cf_list = [ort_cf * (1 + buyume) ** t for t in range(yil)]
            investments.append(Investment(
                ad=ad,
                baslangic_maliyeti=float(maliyet),
                nakit_akislari=cf_list,
                iskonto_orani=iskonto,
            ))

    if st.button("🔀 Karşılaştır", use_container_width=True, key="comp_btn"):
        with st.spinner("Hesaplanıyor..."):
            df = InvestmentEngine.compare(investments)
            st.session_state["comp_df"] = df
            st.session_state["comp_best"] = InvestmentEngine.best(investments)

    if "comp_df" not in st.session_state:
        return

    df   = st.session_state.get("comp_df")
    best = st.session_state.get("comp_best")
    if df is None or df.empty:
        return

    st.markdown(f"""
    <div style="background:#F0FDF4;border:1px solid #05966944;border-radius:10px;
                padding:12px 16px;color:#059669;font-size:0.9rem;margin:12px 0;">
        🏆 En İyi Yatırım: <b>{best}</b>
    </div>""", unsafe_allow_html=True)

    # Tablo
    section_title("📋 Karşılaştırma Tablosu")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Radar karşılaştırması
    section_title("📊 Karşılaştırmalı Grafik")
    fig = go.Figure()
    metrics_cols = ["ROI (%)", "NPV (₺)", "PI", "Skor"]

    for _, row in df.iterrows():
        # Normalize 0-100
        vals = []
        for col in metrics_cols:
            v = row[col]
            if col == "ROI (%)":    vals.append(min(100, max(0, v)))
            elif col == "NPV (₺)":
                max_npv = df["NPV (₺)"].max()
                vals.append(v / max_npv * 100 if max_npv > 0 else 50)
            elif col == "PI":       vals.append(min(100, max(0, (v-0.5)*100)))
            else:                   vals.append(min(100, max(0, v)))

        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=metrics_cols + [metrics_cols[0]],
            name=row["Yatırım"],
            fill="toself", opacity=0.6,
            line=dict(width=2),
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0,100], gridcolor="#E2E8F0",
                            tickfont=dict(color="#64748B", size=8)),
            angularaxis=dict(gridcolor="#E2E8F0",
                             tickfont=dict(color="#94A3B8")),
        ),
        height=380, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("legend","xaxis","yaxis")},
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# MONTE CARLO
# ─────────────────────────────────────────────

def _monte_carlo_ui():
    section_title("🎲 Monte Carlo Risk Simülasyonu")

    if "inv_engine" not in st.session_state:
        st.info("Önce 'Yatırım Analizi' sekmesinde bir yatırım hesaplayın.")
        return

    engine = st.session_state["inv_engine"]

    c1, c2, c3 = st.columns(3)
    with c1: n_sim      = st.select_slider("Simülasyon Sayısı",
                                            options=[1000, 5000, 10000, 50000], value=10000,
                                            key="mc_nsim")
    with c2: nakit_std  = st.slider("Nakit Akışı Belirsizliği (%)", 5, 50, 20,
                                     key="mc_cfstd") / 100
    with c3: maliyet_std= st.slider("Maliyet Belirsizliği (%)", 1, 30, 10,
                                     key="mc_mstd") / 100

    if st.button("🎲 Simülasyonu Çalıştır", use_container_width=True, key="mc_run"):
        with st.spinner(f"{n_sim:,} simülasyon çalıştırılıyor..."):
            mc = engine.monte_carlo(n_sim=n_sim,
                                    nakit_std_pct=nakit_std,
                                    maliyet_std_pct=maliyet_std)
            st.session_state["mc_sonuc"] = mc

    if "mc_sonuc" not in st.session_state:
        return

    mc = st.session_state.get("mc_sonuc", {})
    if not mc or "risk_seviyesi" not in mc:
        st.info("Simülasyonu çalıştırmak için butona tıklayın.")
        return

    # Risk özeti
    risk_renk = {
        "Düşük Risk":       C_GREEN,
        "Orta Risk":        C_YELLOW,
        "Yüksek Risk":      "#f97316",
        "Çok Yüksek Risk":  C_RED,
    }.get(mc["risk_seviyesi"], C_YELLOW)

    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid {risk_renk}44;border-radius:12px;
                padding:14px 18px;margin:8px 0 16px;">
        <span style="color:{risk_renk};font-weight:700;font-size:1rem;">
            ⚠️ {mc["risk_seviyesi"]}
        </span>
        <span style="color:#4B5563;font-size:0.85rem;margin-left:12px;">
            NPV pozitif olma olasılığı: <b style="color:{risk_renk};">
            %{mc["npv_pozitif_oran"]}</b>
        </span>
    </div>""", unsafe_allow_html=True)

    # KPI satırı
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi_card("Ort. NPV",   fmt(mc["npv_ortalama"]),
                      positive=bool(mc["npv_ortalama"]>0))
    with c2: kpi_card("Medyan NPV", fmt(mc["npv_medyan"]),
                      positive=bool(mc["npv_medyan"]>0))
    with c3: kpi_card("NPV P10",    fmt(mc["npv_p10"]),   "Kötümser Senaryo",
                      positive=bool(mc["npv_p10"]>0))
    with c4: kpi_card("NPV P90",    fmt(mc["npv_p90"]),   "İyimser Senaryo",
                      positive=True)

    col1, col2 = st.columns(2)

    with col1:
        section_title("📊 NPV Dağılımı")
        npv_data = np.array(mc["npv_data"])
        fig = go.Figure()
        fig.add_histogram(
            x=npv_data, nbinsx=60,
            marker_color=C_BLUE, opacity=0.8,
            name="NPV Dağılımı",
        )
        fig.add_vline(x=0, line_dash="dash", line_color=C_RED,
                      annotation_text="Başabaş", annotation_font_color=C_RED)
        fig.add_vline(x=mc["npv_ortalama"], line_dash="dot",
                      line_color=C_GREEN,
                      annotation_text="Ortalama", annotation_font_color=C_GREEN)
        fig.update_layout(title=f"{mc['n_sim']:,} Simülasyon",
                          height=300, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("title")})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_title("📊 ROI Dağılımı")
        roi_data = np.array(mc["roi_data"])
        fig = go.Figure()
        fig.add_histogram(
            x=roi_data, nbinsx=60,
            marker_color=C_PURPLE, opacity=0.8,
            name="ROI Dağılımı",
        )
        fig.add_vline(x=0, line_dash="dash", line_color=C_RED)
        fig.add_vline(x=mc["roi_ortalama"], line_dash="dot",
                      line_color=C_GREEN,
                      annotation_text=f'Ort: %{mc["roi_ortalama"]:.1f}',
                      annotation_font_color=C_GREEN)
        fig.update_layout(title="ROI Olasılık Dağılımı",
                          height=300, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("title")})
        st.plotly_chart(fig, use_container_width=True)

    # Güven aralığı tablosu
    section_title("📋 NPV Güven Aralıkları")
    guven_data = pd.DataFrame([
        {"Senaryo": "En Kötü (P10)",  "NPV": fmt(mc["npv_p10"]),  "Olasılık": "%10"},
        {"Senaryo": "Kötümser (P25)", "NPV": fmt(mc["npv_p25"]),  "Olasılık": "%25"},
        {"Senaryo": "Medyan (P50)",   "NPV": fmt(mc["npv_medyan"]),"Olasılık": "%50"},
        {"Senaryo": "İyimser (P75)",  "NPV": fmt(mc["npv_p75"]),  "Olasılık": "%75"},
        {"Senaryo": "En İyi (P90)",   "NPV": fmt(mc["npv_p90"]),  "Olasılık": "%90"},
    ])
    st.dataframe(guven_data, use_container_width=True, hide_index=True)
