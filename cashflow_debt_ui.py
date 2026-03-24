"""
KazKaz AI - Nakit Akışı & Borç Analizi Streamlit Modülü (v13)
==============================================================
app.py entegrasyonu:
    from cashflow_debt_ui import show_cashflow_tab, show_debt_tab
    with tab_nakit:
        show_cashflow_tab(fin_engine, rapor)
    with tab_borc:
        show_debt_tab()
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from design_system import (
    DS, fmt, kpi, sec, exec_summary, alert, page_header, badge,
    inject_css, PLOTLY_THEME, score_color,
    C_BLUE, C_GREEN, C_RED, C_AMBER, C_SLATE, C_CYAN,
    C_YELLOW, C_PURPLE, CHART_COLORS,
)

from cashflow_engine import (
    CashFlowInput, CashFlowEngine, CashFlowForecast
)
from debt_engine import (
    Debt, DebtEngine, DebtType, AmortizationTable
)

# ─────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────

def durum_renk(d):
    return {"İyi":C_GREEN,"Orta":C_YELLOW,"Zayıf":C_RED,
            "Veri Yok":"#64748B","Sağlıklı":C_GREEN,
            "Dikkat":C_YELLOW,"Kritik":C_RED}.get(d, "#94A3B8")

# ══════════════════════════════════════
# NAKİT AKIŞI SEKMESİ
# ══════════════════════════════════════

def show_cashflow_tab(fin_engine=None, fin_rapor=None):
    """Nakit akışı sekmesi."""

    st.markdown(
        '<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#0EA5E9,#1D4ED8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '💧 Nakit Akışı Analizi</div>'
        '<div style="color:#64748B;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'Likidite · Burn Rate · Projeksiyon · Nakit Sağlık Skoru</div>',
        unsafe_allow_html=True)

    sub1, sub2, sub3 = st.tabs([
        "📊 Nakit Akışı",
        "🔥 Burn Rate & Likidite",
        "🔮 Projeksiyon",
    ])

    # ── Parametre girişi ──────────────────────
    with st.expander("⚙️ Nakit Akışı Parametreleri", expanded=fin_engine is None):
        col1, col2 = st.columns(2)
        with col1:
            baslangic = st.number_input(
                "Mevcut Nakit Pozisyonu (₺)", min_value=0,
                value=500_000, step=50_000, key="cf_nakit")
            doven_var = st.number_input(
                "Dönen Varlıklar (₺)", min_value=0,
                value=2_000_000, step=100_000, key="cf_dv")
            kvb = st.number_input(
                "Kısa Vadeli Borçlar (₺)", min_value=0,
                value=800_000, step=50_000, key="cf_kvb")
        with col2:
            stok = st.number_input(
                "Stok Değeri (₺)", min_value=0,
                value=300_000, step=50_000, key="cf_stok")
            alacak_gun = st.slider(
                "Alacak Tahsil Süresi (Gün)", 10, 120, 45, key="cf_alacak")
            borc_gun = st.slider(
                "Borç Ödeme Süresi (Gün)", 10, 120, 30, key="cf_borc")

    # Motor oluştur
    if fin_engine:
        engine = CashFlowEngine.from_financial_engine(
            fin_engine,
            baslangic_nakiti = float(st.session_state.get("cf_nakit", 500_000)),
            donen_varliklar  = float(st.session_state.get("cf_dv", 2_000_000)),
            kisa_vadeli_borc = float(st.session_state.get("cf_kvb", 800_000)),
            stoklar          = float(st.session_state.get("cf_stok", 300_000)),
        )
        engine.inp.alacak_tahsil_suresi = st.session_state.get("cf_alacak", 45)
        engine.inp.borc_odeme_suresi    = st.session_state.get("cf_borc", 30)
        st.session_state.cf_engine = engine
    elif "cf_engine" not in st.session_state:
        st.info("Sol panelden finansal veri yükleyin veya parametreleri girin.")
        return

    engine = st.session_state.get("cf_engine")
    if not engine:
        return
    try:
        rapor = engine.full_report()
    except Exception as ex:
        st.error(f"Nakit akışı hesaplama hatası: {ex}")
        return
    ozet    = rapor["nakit_ozet"]
    liq     = rapor["likidite"]
    burn    = rapor["burn_rate"]
    skor    = rapor["skor"]

    # ──────────────────────────────────────────
    # SUB TAB 1: NAKİT AKIŞI
    # ──────────────────────────────────────────
    with sub1:
        c1,c2,c3,c4 = st.columns(4)
        with c1: kpi("Operasyonel NCF", fmt(ozet["operasyonel_ncf"]),
                     positive=bool(ozet["operasyonel_ncf"]>=0),
                     color=C_GREEN if ozet["operasyonel_ncf"]>=0 else C_RED)
        with c2: kpi("NCF Marjı", f'%{ozet["ncf_marji"]}',
                     positive=bool(ozet["ncf_marji"]>=0),
                     color=C_GREEN if ozet["ncf_marji"]>=0 else C_RED)
        with c3: kpi("Pozitif Ay",
                     f'{ozet["pozitif_ay"]} / {ozet["pozitif_ay"]+ozet["negatif_ay"]}',
                     positive=bool(ozet["pozitif_ay"]>ozet["negatif_ay"]))
        with c4:
            renk = score_color(skor["kategori"])
            kpi("Nakit Sağlık", f'{skor["skor"]}/100', delta=skor["kategori"], color=renk, positive=bool(skor["skor"]>=50))

        st.markdown("---")

        # Nakit akışı grafiği
        tablo = rapor["aylik_tablo"]
        sec("📊 Aylık Nakit Akışı")
        fig = go.Figure()
        fig.add_bar(x=tablo["Dönem"], y=tablo["Nakit Girişi"],
                    name="Giriş", marker_color=C_GREEN, opacity=.8)
        fig.add_bar(x=tablo["Dönem"], y=[-v for v in tablo["Nakit Çıkışı"]],
                    name="Çıkış", marker_color=C_RED, opacity=.8)
        fig.add_scatter(x=tablo["Dönem"], y=tablo["Net Nakit"],
                        name="Net", mode="lines+markers",
                        line=dict(color=C_CYAN, width=2.5),
                        marker=dict(size=7))
        fig.add_hline(y=0, line_dash="dash", line_color="#64748B", opacity=.5)
        fig.update_layout(barmode="relative", height=290, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("legend","xaxis","yaxis")},
                          legend=dict(orientation="h",y=1.1,x=0))
        st.plotly_chart(fig, use_container_width=True)

        # Kümülatif
        sec("📈 Kümülatif Nakit Pozisyonu")
        colors_kum = [C_GREEN if v>=0 else C_RED for v in tablo["Kümülatif"]]
        fig2 = go.Figure(go.Scatter(
            x=tablo["Dönem"], y=tablo["Kümülatif"],
            fill="tozeroy", mode="lines+markers",
            line=dict(color=C_BLUE, width=2.5),
            fillcolor="rgba(0,102,255,0.08)",
            marker=dict(color=colors_kum, size=8),
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color=C_RED, opacity=.6)
        fig2.update_layout(height=230, **PLOTLY_THEME)
        st.plotly_chart(fig2, use_container_width=True)

        # Özet tablo
        sec("📋 Aylık Nakit Akışı Tablosu")
        st.dataframe(
            tablo.style.format({
                "Nakit Girişi": "{:,.0f} ₺",
                "Nakit Çıkışı": "{:,.0f} ₺",
                "Net Nakit":    "{:,.0f} ₺",
                "Kümülatif":    "{:,.0f} ₺",
            }).map(
                lambda v: "color:#059669" if isinstance(v,(int,float)) and v>=0
                          else "color:#DC2626" if isinstance(v,(int,float)) and v<0
                          else "",
                subset=["Net Nakit","Kümülatif"]
            ),
            use_container_width=True, hide_index=True
        )

    # ──────────────────────────────────────────
    # SUB TAB 2: BURN RATE & LİKİDİTE
    # ──────────────────────────────────────────
    with sub2:
        # Burn rate
        sec("🔥 Burn Rate Analizi")
        burn_renk = {"Güvenli":C_GREEN,"Dikkat":C_YELLOW,
                     "Kritik":C_RED,"Nakit Yok":"#64748B"}.get(
                     burn["durum"], C_YELLOW)

        c1,c2,c3,c4 = st.columns(4)
        with c1: kpi("Brüt Yakma Hızı", fmt(burn["brut_yakma_hizi"]), delta="Aylık ortalama çıkış", color=C_RED, positive=False)
        with c2: kpi("Net Yakma Hızı", fmt(abs(burn["net_yakma_hizi"])), delta="Aylık nakit değişimi", color=C_GREEN if burn["net_yakma_hizi"]>=0 else C_RED,
                     positive=bool(burn["net_yakma_hizi"]>=0))
        with c3:
            runway = burn["runway_ay"]
            kpi("Runway", f'{runway:.0f} Ay' if runway else "∞", delta=burn["durum"], color=burn_renk,
                positive=bool(not burn["nakit_yakilip_yakilmiyor"]))
        with c4: kpi("Verimlilik Oranı", str(burn["verimlilik_orani"]), delta="> 1 iyi", color=C_GREEN if burn["verimlilik_orani"]>=1 else C_RED,
                     positive=bool(burn["verimlilik_orani"]>=1))

        # Likidite
        st.markdown("---")
        sec("💧 Likidite Oranları")
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            cr = liq["cari_oran"]
            kpi("Cari Oran", str(cr) if cr else "Veri Yok", delta="Hedef: > 2", color=durum_renk(liq["cari_oran_durum"]),
                positive=bool(liq["cari_oran_durum"]=="İyi"))
        with c2:
            qr = liq["asit_oran"]
            kpi("Asit-Test Oranı", str(qr) if qr else "Veri Yok", delta="Hedef: > 1", color=durum_renk(liq["asit_oran_durum"]),
                positive=bool(liq["asit_oran_durum"]=="İyi"))
        with c3:
            kpi("Net İşletme Ser.", fmt(liq["net_isletme_ser"]),
                positive=bool(liq["net_isletme_ser"]>=0),
                color=C_GREEN if liq["net_isletme_ser"]>=0 else C_RED)
        with c4:
            ccc = liq["nakit_donusum_gun"]
            kpi("Nakit Dönüşüm", f'{ccc} Gün', delta=liq["ccc_durum"], color=durum_renk(liq["ccc_durum"]),
                positive=bool(ccc<=30))

        # Likidite radar
        col1, col2 = st.columns(2)
        with col1:
            sec("📡 Likidite Radar")
            if liq["cari_oran"] and liq["asit_oran"]:
                labels = ["Cari Oran","Asit-Test","Net İşl.Ser.","CCC Verimi"]
                values = [
                    min(liq["cari_oran"]/3*100, 100),
                    min(liq["asit_oran"]/2*100, 100),
                    min(max(liq["net_isletme_ser"]/1_000_000*50+50, 0), 100),
                    max(0, 100 - liq["nakit_donusum_gun"]),
                ]
                fig = go.Figure(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=labels + [labels[0]],
                    fill="toself",
                    fillcolor="rgba(0,212,255,0.12)",
                    line=dict(color=C_CYAN, width=2),
                    marker=dict(size=7),
                ))
                fig.update_layout(
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(range=[0,100], gridcolor="#E2E8F0",
                                        tickfont=dict(color="#64748B",size=8)),
                        angularaxis=dict(gridcolor="#E2E8F0",
                                         tickfont=dict(color="#94A3B8",size=9)),
                    ),
                    height=280, **PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dönen varlık ve KVB bilgisi girilirse likidite oranları hesaplanır.")

        with col2:
            sec("📋 Likidite Özeti")
            lik_df = pd.DataFrame([
                {"Metrik": "Cari Oran",         "Değer": str(liq["cari_oran"]),
                 "Hedef":">2",   "Durum": liq["cari_oran_durum"]},
                {"Metrik": "Asit-Test Oranı",   "Değer": str(liq["asit_oran"]),
                 "Hedef":">1",   "Durum": liq["asit_oran_durum"]},
                {"Metrik": "Nakit Oranı",        "Değer": str(liq["nakit_oran"]),
                 "Hedef":">0.2", "Durum": liq["cash_oran_durum"]},
                {"Metrik": "Alacak Tahsil (Gün)","Değer": str(liq["alacak_tahsil_gun"]),
                 "Hedef":"<45",  "Durum": "İyi" if liq["alacak_tahsil_gun"]<=45 else "Orta"},
                {"Metrik": "Borç Ödeme (Gün)",   "Değer": str(liq["borc_odeme_gun"]),
                 "Hedef":">30",  "Durum": "İyi" if liq["borc_odeme_gun"]>=30 else "Orta"},
                {"Metrik": "Nakit Dönüşüm (Gün)","Değer": str(liq["nakit_donusum_gun"]),
                 "Hedef":"<30",  "Durum": liq["ccc_durum"]},
            ])
            def color_d(val):
                c = {"İyi":C_GREEN,"Orta":C_YELLOW,"Zayıf":C_RED,
                     "Sağlıklı":C_GREEN,"Dikkat":C_YELLOW,"Kritik":C_RED}.get(val,"")
                return f"color:{c};font-weight:600" if c else ""
            st.dataframe(
                lik_df.style.map(color_d, subset=["Durum"]),
                use_container_width=True, hide_index=True)

    # ──────────────────────────────────────────
    # SUB TAB 3: PROJEKSİYON
    # ──────────────────────────────────────────
    with sub3:
        sec("🔮 Kısa Vadeli Nakit Akışı Projeksiyonu")

        buyume = st.slider("Aylık Büyüme Beklentisi (%)", -10, 30, 3,
                           key="cf_buyume") / 100
        ay = st.slider("Projeksiyon Süresi (Ay)", 1, 12, 3, key="cf_proj_ay")

        fc  = CashFlowForecast(engine.inp, tahmin_ay=ay)
        iyi = fc.optimistic()
        baz = fc.base()
        kot = fc.pessimistic()
        ozel= fc.project(buyume_orani=buyume)

        # Grafik
        fig = go.Figure()
        fig.add_scatter(x=iyi["Dönem"], y=iyi["Kümülatif"],
                        name="İyimser (+%10)", mode="lines+markers",
                        line=dict(color=C_GREEN, width=2, dash="dot"),
                        marker=dict(size=6))
        fig.add_scatter(x=baz["Dönem"], y=baz["Kümülatif"],
                        name="Baz (+%3)", mode="lines+markers",
                        line=dict(color=C_BLUE, width=2.5),
                        marker=dict(size=7))
        fig.add_scatter(x=kot["Dönem"], y=kot["Kümülatif"],
                        name="Kötümser (-%5)", mode="lines+markers",
                        line=dict(color=C_RED, width=2, dash="dot"),
                        marker=dict(size=6))
        if buyume not in [0.10, 0.03, -0.05]:
            fig.add_scatter(x=ozel["Dönem"], y=ozel["Kümülatif"],
                            name=f"Özel (%{buyume*100:.0f})", mode="lines+markers",
                            line=dict(color=C_YELLOW, width=2, dash="dash"),
                            marker=dict(size=6))
        fig.add_hline(y=0, line_dash="dash", line_color="#64748B", opacity=.5)
        fig.update_layout(title="Kümülatif Nakit Projeksiyon Senaryoları",
                          height=300, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("legend","xaxis","yaxis")},
                          legend=dict(orientation="h",y=1.12,x=0))
        st.plotly_chart(fig, use_container_width=True)

        # Tablo
        sec("📋 Projeksiyon Tablosu (Baz Senaryo)")
        st.dataframe(
            baz.style.format({
                "Proj. Giriş": "{:,.0f} ₺",
                "Proj. Çıkış": "{:,.0f} ₺",
                "Net":         "{:,.0f} ₺",
                "Kümülatif":   "{:,.0f} ₺",
            }).map(
                lambda v: "color:#059669" if isinstance(v,(int,float)) and v>=0
                          else "color:#DC2626" if isinstance(v,(int,float)) and v<0
                          else "",
                subset=["Net","Kümülatif"]
            ),
            use_container_width=True, hide_index=True)

# ══════════════════════════════════════
# BORÇ ANALİZİ SEKMESİ
# ══════════════════════════════════════

def show_debt_tab(fin_rapor=None):
    """Borç analizi sekmesi."""

    st.markdown(
        '<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#0EA5E9,#1D4ED8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '🏦 Borç Analizi</div>'
        '<div style="color:#64748B;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'DSCR · Faiz Karşılama · İtfa Tablosu · Borç Kapasitesi</div>',
        unsafe_allow_html=True)

    # ── Borç giriş formu ──
    sec("📝 Borç Portföyü")

    n_borc = st.number_input("Borç Sayısı", min_value=1, max_value=10,
                              value=2, key="debt_n")

    debts = []
    for i in range(int(n_borc)):
        with st.expander(f"💳 Borç {i+1}", expanded=(i==0)):
            c1,c2,c3 = st.columns(3)
            with c1:
                ad      = st.text_input("Borç Adı", f"Kredi {i+1}", key=f"d_ad_{i}")
                anapara = st.number_input("Kalan Anapara (₺)",
                                          min_value=0, value=500_000, step=10_000,
                                          key=f"d_ana_{i}")
            with c2:
                faiz    = st.slider("Yıllık Faiz (%)", 1, 100, 40, key=f"d_faiz_{i}") / 100
                vade    = st.slider("Kalan Vade (Ay)", 1, 120, 24, key=f"d_vade_{i}")
            with c3:
                tur     = st.selectbox("Borç Türü",
                                       [t.value for t in DebtType],
                                       key=f"d_tur_{i}")
                teminat = st.text_input("Teminat (opsiyonel)", "", key=f"d_tem_{i}")

            try:
                debts.append(Debt(
                    ad=ad, anapara=float(anapara),
                    faiz_orani=faiz, vade_ay=vade,
                    borc_turu=tur, teminat=teminat
                ))
            except Exception as e:
                st.error(f"Borç {i+1} hata: {e}")

    st.markdown("---")
    sec("📊 Finansal Bilgiler")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        yillik_gelir = st.number_input("Yıllık Gelir (₺)",
                                        min_value=0, value=5_000_000,
                                        step=100_000, key="d_gelir")
    with c2:
        yillik_favok = st.number_input("Yıllık FAVÖK (₺)",
                                        min_value=0, value=800_000,
                                        step=50_000, key="d_favok")
    with c3:
        toplam_varlik = st.number_input("Toplam Varlık (₺)",
                                         min_value=0, value=8_000_000,
                                         step=100_000, key="d_varlik")
    with c4:
        ozkaynaklar = st.number_input("Özkaynak (₺)",
                                       min_value=0, value=3_000_000,
                                       step=100_000, key="d_ozkaynak")

    if st.button("🏦 Borç Analizini Hesapla", use_container_width=True):
        if not debts:
            st.warning("En az bir borç girilmeli.")
            return
        try:
            engine = DebtEngine(
                debts          = debts,
                yillik_gelir   = float(yillik_gelir),
                yillik_favok   = float(yillik_favok),
                toplam_varlik  = float(toplam_varlik),
                ozkaynaklar    = float(ozkaynaklar),
            )
            st.session_state.debt_engine = engine
            st.session_state.debt_rapor  = engine.full_report()
        except Exception as e:
            st.error(f"Hesaplama hatası: {e}")

    if "debt_rapor" not in st.session_state:
        return

    rapor   = st.session_state.debt_rapor
    engine  = st.session_state.debt_engine
    port    = rapor["portfolio_ozet"]
    metrik  = rapor["metrikler"]
    skor    = rapor["skor"]
    kapasite= rapor["kapasite"]

    st.markdown("---")

    # KPI satırı
    c1,c2,c3,c4 = st.columns(4)
    sk_renk = score_color(skor["kategori"])
    with c1: kpi("Toplam Borç",    fmt(port["toplam_borc"]),
                 positive=False, color=C_RED)
    with c2: kpi("Aylık Taksit",   fmt(port["aylik_taksit"]),
                 f'Yıllık: {fmt(port["aylik_taksit"]*12)}',
                 color=C_YELLOW, positive=False)
    with c3: kpi("Ağ. Faiz Oranı", f'%{port["agirlikli_faiz"]}', delta=f'{port["borc_sayisi"]} borç kalemi', color=C_RED if port["agirlikli_faiz"]>40 else C_YELLOW,
                 positive=bool(port["agirlikli_faiz"]<=30))
    with c4: kpi("Borç Skoru", f'{skor["skor"]}/100', delta=skor["kategori"], color=sk_renk,
                 positive=bool(skor["skor"]>=50))

    st.markdown(
        f'<div style="background:#F8FAFC;border:1px solid #BFDBFE;'
        f'border-radius:12px;padding:12px 18px;color:#475569;'
        f'font-size:.87rem;margin:10px 0;">'
        f'💡 {skor["tavsiye"]}</div>', unsafe_allow_html=True)

    sub1, sub2, sub3 = st.tabs([
        "📊 Borç Metrikleri",
        "📋 İtfa Tablosu",
        "💡 Kapasite & Öncelik",
    ])

    # ──────────────────────────────────────────
    # BORÇ METRİKLERİ
    # ──────────────────────────────────────────
    with sub1:
        col1, col2 = st.columns(2)
        with col1:
            sec("🎯 Temel Borç Oranları")
            metrik_df = pd.DataFrame([
                {"Metrik":"DSCR (Borç Servis Karşılama)",
                 "Değer": str(metrik["dscr"]),
                 "Hedef": "> 1.25", "Durum": metrik["dscr_durum"]},
                {"Metrik":"Faiz Karşılama Oranı",
                 "Değer": str(metrik["faiz_karsilama"]),
                 "Hedef": "> 3",    "Durum": metrik["ic_durum"]},
                {"Metrik":"Kaldıraç Oranı (Net Borç/FAVÖK)",
                 "Değer": str(metrik["kaldirac_orani"]),
                 "Hedef": "< 3",    "Durum": metrik["lev_durum"]},
                {"Metrik":"Aylık Taksit/Gelir Oranı (%)",
                 "Değer": str(metrik["aylik_yuk_pct"]),
                 "Hedef": "< 30%",  "Durum": metrik["mb_durum"]},
                {"Metrik":"Borç/Özkaynak",
                 "Değer": str(metrik["borc_ozkaynak"]),
                 "Hedef": "< 2",    "Durum": "İyi" if (metrik["borc_ozkaynak"] or 99)<2 else "Orta"},
                {"Metrik":"Borç/Varlık",
                 "Değer": str(metrik["borc_varlik"]),
                 "Hedef": "< 0.5",  "Durum": "İyi" if (metrik["borc_varlik"] or 1)<0.5 else "Orta"},
            ])
            def color_d(v):
                c = {"İyi":C_GREEN,"Orta":C_YELLOW,"Zayıf":C_RED,
                     "Veri Yok":"#64748B"}.get(v,"")
                return f"color:{c};font-weight:600" if c else ""
            st.dataframe(
                metrik_df.style.map(color_d, subset=["Durum"]),
                use_container_width=True, hide_index=True)

        with col2:
            sec("📊 Borç Türü Dağılımı")
            tur_df = rapor["tur_dagilimi"]
            if not tur_df.empty:
                fig = px.pie(tur_df, values="Tutar", names="Tür",
                             color_discrete_sequence=[
                                 C_RED,"#1D4ED8","#374151","#0F766E",
                                 "#6B7280","#1D4ED8"],
                             hole=0.5)
                fig.update_layout(height=280, **PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)

        # Borç özet tablosu
        sec("📋 Borç Portföyü Özeti")
        ozet_df = rapor["ozet_tablo"]
        st.dataframe(
            ozet_df.style.format({
                "Kalan Anapara": "{:,.0f} ₺",
                "Aylık Taksit":  "{:,.0f} ₺",
                "Toplam Faiz":   "{:,.0f} ₺",
                "Toplam Ödeme":  "{:,.0f} ₺",
                "Faiz (%)":      "{:.1f}%",
            }),
            use_container_width=True, hide_index=True)

    # ──────────────────────────────────────────
    # İTFA TABLOSU
    # ──────────────────────────────────────────
    with sub2:
        sec("📅 İtfa Tablosu")
        borç_adlari = [d.ad for d in engine.portfolio.debts]
        secili = st.selectbox("Borç Seçin", borç_adlari, key="amort_sec")
        idx    = borç_adlari.index(secili)
        amort  = engine.amortization_schedule(idx)
        debt   = engine.portfolio.debts[idx]
        amort_obj = AmortizationTable(debt)

        c1,c2,c3 = st.columns(3)
        with c1: kpi("Toplam Ödenecek",   fmt(amort_obj.total_payment()),
                     color=C_YELLOW, positive=False)
        with c2: kpi("Toplam Faiz",       fmt(amort_obj.total_interest()),
                     color=C_RED, positive=False)
        with c3: kpi("Faiz/Anapara Oranı",
                     f'%{round(amort_obj.total_interest()/max(debt.anapara,1)*100,1)}',
                     color=C_YELLOW, positive=False)

        # Alan grafik (anapara vs faiz)
        fig = go.Figure()
        fig.add_scatter(x=amort["Ay"], y=amort["Kalan Anapara"],
                        name="Kalan Anapara", fill="tozeroy",
                        mode="lines", line=dict(color=C_RED, width=2),
                        fillcolor="rgba(255,71,87,0.1)")
        fig.add_bar(x=amort["Ay"], y=amort["Faiz Ödemesi"],
                    name="Faiz", marker_color=C_YELLOW, opacity=.8, yaxis="y2")
        fig.add_bar(x=amort["Ay"], y=amort["Anapara Ödemesi"],
                    name="Anapara", marker_color=C_GREEN, opacity=.8, yaxis="y2")
        fig.update_layout(
            barmode="stack", height=290,
            yaxis2=dict(overlaying="y", side="right",
                        gridcolor="#E2E8F0"),
            legend=dict(orientation="h",y=1.1,x=0), **PLOTLY_THEME)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            amort.style.format({
                "Taksit":           "{:,.0f} ₺",
                "Anapara Ödemesi":  "{:,.0f} ₺",
                "Faiz Ödemesi":     "{:,.0f} ₺",
                "Kalan Anapara":    "{:,.0f} ₺",
            }),
            use_container_width=True, hide_index=True)

    # ──────────────────────────────────────────
    # KAPASİTE & ÖNCELİK
    # ──────────────────────────────────────────
    with sub3:
        col1, col2 = st.columns(2)
        with col1:
            sec("💡 Borç Kapasitesi")
            kap = kapasite
            st.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                f'border-radius:12px;padding:16px 20px;margin-bottom:12px;">'
                f'<div style="color:#64748B;font-size:.75rem;letter-spacing:1.5px;'
                f'text-transform:uppercase;margin-bottom:10px;">Kullanım Oranı</div>'
                f'<div style="background:#E2E8F0;border-radius:8px;height:12px;overflow:hidden;">'
                f'<div style="background:linear-gradient(90deg,{C_BLUE},{C_CYAN});'
                f'width:{min(kap["kullanim_orani"],100)}%;height:100%;'
                f'border-radius:8px;"></div></div>'
                f'<div style="color:#0F172A;font-size:1.1rem;font-weight:700;'
                f'margin-top:8px;">%{kap["kullanim_orani"]}</div>'
                f'</div>', unsafe_allow_html=True)
            kpi("Mevcut Borç",    fmt(kap["mevcut_borc"]), positive=False)
            kpi("Ek Borç Kapasitesi", fmt(kap["maks_ek_borc"]), delta="DSCR≥1.25 koşulunda", color=C_GREEN if kap["maks_ek_borc"]>0 else C_RED,
                positive=bool(kap["maks_ek_borc"]>0))
            st.markdown(
                f'<div style="background:#F0FDF4;border-left:3px solid #059669;'
                f'border-radius:0 8px 8px 0;padding:10px 14px;'
                f'color:#065F46;font-size:.86rem;margin-top:8px;">'
                f'💡 {kap["tavsiye"]}</div>', unsafe_allow_html=True)

        with col2:
            sec("🏅 Ödeme Önceliği (Avalanche)")
            st.markdown(
                '<div style="color:#64748B;font-size:.8rem;margin-bottom:10px;">'
                'Yüksek faizli borcu önce ödemek toplam maliyeti düşürür.</div>',
                unsafe_allow_html=True)
            onc_df = rapor["odeme_onceligi"]
            st.dataframe(
                onc_df.style.format({
                    "Kalan Anapara": "{:,.0f} ₺",
                    "Toplam Faiz":   "{:,.0f} ₺",
                    "Faiz (%)":      "{:.1f}%",
                }).map(
                    lambda v: "color:#DC2626;font-weight:700"
                    if v == 1 else "",
                    subset=["Öncelik"]
                ),
                use_container_width=True, hide_index=True)
