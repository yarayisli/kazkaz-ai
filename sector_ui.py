"""
KazKaz AI - Sektör Karşılaştırması Streamlit Modülü (v14)
==========================================================
app.py entegrasyonu:
    from sector_ui import show_sector_tab
    with tab_sektor:
        show_sector_tab(df, rapor, sirket_adi, gemini)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from design_system import (
    DS, fmt, kpi, sec, exec_summary, alert, page_header,
    badge, PLOTLY_THEME,
    C_BLUE, C_GREEN, C_RED, C_AMBER, C_SLATE, C_CYAN,
    C_YELLOW, C_PURPLE, CHART_COLORS, score_color
)


from sector_engine import SectorEngine, SECTOR_DB, GENEL_SEKTOR


# ─────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────


def badge_color(durum: str) -> str:
    return {"Mükemmel":"#059669","İyi":"#3B82F6",
            "Orta":"#D97706","Zayıf":"#DC2626"}.get(durum,"#94A3B8")

def pt_merge(**overrides):
    """PT temasını override parametrelerle birleştirir."""
    merged = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8", family="Inter"),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    merged.update(overrides)
    return merged

    return {"Sektör Lideri":"#059669","Ortalamanın Üstü":"#3B82F6",
            "Sektör Ortalaması":"#D97706","Ortalamanın Altı":"#f97316",
            "Sektörde Zayıf":"#DC2626"}.get(k,"#0F172A")


# ─────────────────────────────────────────────
# ANA FONKSİYON
# ─────────────────────────────────────────────

def show_sector_tab(df, rapor, sirket_adi="Şirketim", gemini=None):
    """app.py'deki sektör sekmesine mount edilir."""

    st.markdown(
        '<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#0EA5E9,#1D4ED8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '🏭 Sektör Karşılaştırması</div>'
        '<div style="color:#64748B;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:20px;">'
        'Benchmark · Rakip Analizi · Sektör Trendi</div>',
        unsafe_allow_html=True)

    # ── Motor başlat / cache ──
    if ("sector_engine" not in st.session_state or
            st.session_state.get("sector_sirket") != sirket_adi):
        with st.spinner("Sektör analizi yapılıyor..."):
            se = SectorEngine(df, rapor, sirket_adi)
            st.session_state.sector_engine = se
            st.session_state.sector_sirket = sirket_adi
    else:
        se = st.session_state.sector_engine

    # ── Manuel sektör seçimi ──
    sektorler     = ["Otomatik Tespit"] + SectorEngine.list_sectors()
    secili_index  = 0
    if st.session_state.get("sector_override"):
        try:
            secili_index = sektorler.index(st.session_state.sector_override)
        except ValueError:
            secili_index = 0

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        secim = st.selectbox(
            "Sektör Seçimi",
            options=sektorler,
            index=secili_index,
            key="sector_select",
            help="Otomatik tespit doğru değilse manuel seçin.",
        )
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🔄 Analizi Yenile", use_container_width=True):
            if secim != "Otomatik Tespit":
                se.override_sector(secim)
                st.session_state.sector_override = secim
            else:
                st.session_state.sector_override = None
                se = SectorEngine(df, rapor, sirket_adi)
                st.session_state.sector_engine = se
            st.session_state.pop("sector_rapor", None)
            st.rerun()

    # ── Rapor üret (cache) ──
    if "sector_rapor" not in st.session_state:
        with st.spinner("Benchmark hesaplanıyor..."):
            try:
                st.session_state.sector_rapor = se.full_report()
            except Exception as ex:
                st.error(f"Sektör analizi hatası: {ex}")
                return

    sr = st.session_state.get("sector_rapor")
    if not sr:
        return
    tespit = sr["tespit"]
    bm     = sr["benchmark"]
    rakip  = sr["rakip"]
    sbilgi = sr["sektor_bilgi"]

    # ── Sektör tespit kartı ──
    guven_renk = "#059669" if tespit["guven"]>=0.7 else "#D97706" if tespit["guven"]>=0.4 else "#f97316"
    st.markdown(
        f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
        f'border-radius:14px;padding:16px 20px;margin-bottom:20px;">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<span style="font-size:2rem;">{tespit["emoji"]}</span>'
        f'<div>'
        f'<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.1rem;'
        f'font-weight:700;color:#0F172A;">{tespit["sektor"]}</div>'
        f'<div style="color:#64748B;font-size:.8rem;">{tespit["aciklama"]}</div>'
        f'</div>'
        f'<div style="margin-left:auto;text-align:right;">'
        f'<div style="color:{guven_renk};font-size:.85rem;font-weight:600;">'
        f'Güven: %{int(tespit["guven"]*100)}</div>'
        f'<div style="color:#64748B;font-size:.75rem;">{tespit["metod"]}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True)

    # ── Alt sekmeler ──
    s1, s2, s3, s4 = st.tabs([
        "📊 Benchmark",
        "🏆 Rakip Analizi",
        "📈 Sektör Trendi",
        "🔍 Detaylı Analiz",
    ])

    # ════════════════════════════════
    # BENCHMARK
    # ════════════════════════════════
    with s1:
        renk = score_color(bm["kategori"])

        # Genel skor
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            kpi("Benchmark Skoru", f'{bm["genel_skor"]}/100', delta=bm["kategori"], color=renk, positive=bool(bm["genel_skor"]>=50))
        with c2:
            kpi("Sektör", tespit["sektor"], delta=tespit["emoji"], color="#3B82F6", positive=True)
        with c3:
            kpi("Güçlü Yönler", str(len(bm["guclu_yonler"])), delta="Sektör ortalaması üstü", color="#059669",
                positive=bool(len(bm["guclu_yonler"]))>0)
        with c4:
            kpi("Gelişim Alanı", str(len(bm["zayif_yonler"])), delta="Sektör ortalaması altı", color="#D97706",
                positive=bool(len(bm["zayif_yonler"]))==0)

        st.markdown("---")

        # Metrik radar
        col1, col2 = st.columns(2)
        with col1:
            sec("📡 Benchmark Radar")
            alt = bm["alt_skorlar"]
            labels = list(alt.keys())
            tr_labels = {
                "kar_marji":"Kar Marjı","gelir_buyumesi":"Büyüme",
                "gider_gelir_orani":"Gider Kontrolü",
                "aylik_gelir":"Gelir Büyüklüğü","operasyonel_marj":"Op. Marj",
            }
            display_labels = [tr_labels.get(l,l) for l in labels]
            values = [alt[l] for l in labels]

            fig = go.Figure()
            fig.add_scatterpolar(
                r=values + [values[0]],
                theta=display_labels + [display_labels[0]],
                fill="toself", fillcolor="rgba(0,102,255,0.15)",
                line=dict(color="#1D4ED8",width=2.5),
                name="Şirketiniz",
            )
            fig.add_scatterpolar(
                r=[50]*len(labels) + [50],
                theta=display_labels + [display_labels[0]],
                fill="toself", fillcolor="rgba(255,255,255,0.03)",
                line=dict(color="#64748B",width=1,dash="dot"),
                name="Sektör Ortalaması",
            )
            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(range=[0,100],gridcolor="#E2E8F0",
                                    tickfont=dict(color="#64748B",size=8)),
                    angularaxis=dict(gridcolor="#E2E8F0",
                                     tickfont=dict(color="#94A3B8",size=9)),
                ),
                height=320, **PT,
                legend=dict(orientation="h",y=-0.15,x=0.5,xanchor="center"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            sec("📋 Metrik Karşılaştırma Tablosu")
            metrik_rows = []
            tr_names = {
                "kar_marji":"Kar Marjı","gelir_buyumesi":"Gelir Büyümesi",
                "gider_gelir_orani":"Gider/Gelir Oranı",
                "aylik_gelir":"Aylık Gelir","operasyonel_marj":"Operasyonel Marj",
            }
            for mk, mv in bm["metrik_sonuclari"].items():
                birim = mv["birim"]
                def _f(v, b):
                    return fmt(v) if b=="₺" else f"%{v:.1f}"
                metrik_rows.append({
                    "Metrik":       tr_names.get(mk, mk),
                    "Sizin Değer":  _f(mv["sirket_degeri"], birim),
                    "Sektör İyi":   _f(mv["sektor_iyi"], birim),
                    "Sektör Ort.":  _f(mv["sektor_orta"], birim),
                    "Durum":        mv["durum"],
                    "Skor":         mv["skor"],
                })
            df_bm = pd.DataFrame(metrik_rows)

            def color_durum(val):
                c = {"Mükemmel":"#059669","İyi":"#3B82F6",
                     "Orta":"#D97706","Zayıf":"#DC2626"}.get(val,"")
                return f"color: {c}" if c else ""

            st.dataframe(
                df_bm.style.map(color_durum, subset=["Durum"])
                           .format({"Skor": "{:.0f}"}),
                use_container_width=True, hide_index=True,
            )

        # Güçlü/zayıf yönler
        col1, col2 = st.columns(2)
        with col1:
            if bm["guclu_yonler"]:
                sec("✅ Güçlü Yönler")
                for g in bm["guclu_yonler"]:
                    st.markdown(
                        f'<div style="background:#F0FDF4;border-left:3px solid #059669;'
                        f'border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:6px;'
                        f'color:#065F46;font-size:.85rem;">✅ {g}</div>',
                        unsafe_allow_html=True)
        with col2:
            if bm["zayif_yonler"]:
                sec("⚠️ Gelişim Alanları")
                for z in bm["zayif_yonler"]:
                    st.markdown(
                        f'<div style="background:#1a1000;border-left:3px solid #D97706;'
                        f'border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:6px;'
                        f'color:#e8c860;font-size:.85rem;">⚠️ {z}</div>',
                        unsafe_allow_html=True)

        # Tavsiyeler
        if bm["tavsiyeler"]:
            sec("💡 Tavsiyeler")
            for i, t in enumerate(bm["tavsiyeler"], 1):
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'border-radius:10px;padding:10px 14px;margin-bottom:6px;'
                    f'color:#475569;font-size:.86rem;">'
                    f'<b style="color:#1D4ED8;">{i}.</b> {t}</div>',
                    unsafe_allow_html=True)

        # AI Benchmark Yorumu
        if gemini:
            st.markdown("---")
            if st.button("🤖 AI Benchmark Yorumu Al", key="ai_bm_btn"):
                with st.spinner("Gemini yorumlıyor..."):
                    prompt_data = {
                        "gelir": rapor["gelir"],
                        "karlilik": rapor["karlilik"],
                        "saglik_skoru": rapor["saglik_skoru"],
                    }
                    yorum_prompt = (
                        f"Şirket '{sirket_adi}' {tespit['sektor']} sektöründe faaliyet gösteriyor. "
                        f"Benchmark skoru {bm['genel_skor']}/100 ({bm['kategori']}). "
                        f"Güçlü yönler: {', '.join(bm['guclu_yonler'][:2]) if bm['guclu_yonler'] else 'Yok'}. "
                        f"Zayıf yönler: {', '.join(bm['zayif_yonler'][:2]) if bm['zayif_yonler'] else 'Yok'}. "
                        f"Bu sektör karşılaştırması sonuçlarını yöneticiye özel yorumla ve 3 stratejik öneri ver."
                    )
                    try:
                        yorum = gemini.model.generate_content(yorum_prompt).text
                        st.session_state["sector_ai_yorum"] = yorum
                    except Exception as e:
                        st.error(f"AI hatası: {e}")

            if "sector_ai_yorum" in st.session_state:
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #BFDBFE;'
                    f'border-radius:14px;padding:18px 22px;color:#334155;'
                    f'font-size:.9rem;line-height:1.8;">'
                    f'<span style="display:inline-block;background:#1D4ED822;'
                    f'border:1px solid #BFDBFE;color:#1D4ED8;font-size:.7rem;'
                    f'letter-spacing:0.1em;text-transform:uppercase;padding:3px 10px;'
                    f'border-radius:20px;margin-bottom:10px;">Gemini AI</span><br>'
                    f'{st.session_state["sector_ai_yorum"].replace(chr(10),"<br>")}'
                    f'</div>',
                    unsafe_allow_html=True)

    # ════════════════════════════════
    # RAKİP ANALİZİ
    # ════════════════════════════════
    with s2:
        sec("🏆 Rakip Karşılaştırması")

        rank = rakip
        df_r = rank["df"]

        # Sıralama özeti
        yuzdelik = rank["yuzdelik"]
        y_renk   = "#059669" if yuzdelik>=70 else "#D97706" if yuzdelik>=40 else "#DC2626"

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi("Sektör Rakip Sayısı", str(rank["toplam_rakip"]), delta=f'{tespit["sektor"]} sektörü', color="#3B82F6")
        with c2:
            kpi("Kar Marjı Sıralaması", f'{rank["kar_marji_sira"]}. / {rank["toplam_rakip"]+1}', delta="Rakipler arasında", color=y_renk,
                positive=bool(rank["kar_marji_sira"] <= rank["toplam_rakip"]//2 + 1))
        with c3:
            kpi("Yüzdelik Dilim", f'%{int(yuzdelik)}', delta="Üst %: daha iyi", color=y_renk,
                positive=bool(yuzdelik>=50))

        st.markdown("---")

        # Tablo
        sec("📋 Rakip Karşılaştırma Tablosu")

        def highlight_sirket(row):
            if "★" in str(row["Şirket"]):
                return ["background-color: #0a1e3a; color: #60d4ff; font-weight: bold"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_r.style.apply(highlight_sirket, axis=1)
                      .format({
                          "Kar Marjı (%)":   "{:.1f}%",
                          "Büyüme (%)":      "{:.1f}%",
                          "Gider/Gelir (%)": "{:.1f}%",
                          "Aylık Gelir (₺)": lambda v: fmt(v),
                      }),
            use_container_width=True, hide_index=True,
        )

        # Bar karşılaştırma
        sec("📊 Kar Marjı Karşılaştırması")
        df_sorted = df_r.sort_values("Kar Marjı (%)", ascending=True)
        bar_colors = [
            "#1D4ED8" if "★" in str(s) else "#E2E8F0"
            for s in df_sorted["Şirket"]
        ]
        fig = go.Figure(go.Bar(
            x=df_sorted["Kar Marjı (%)"],
            y=df_sorted["Şirket"],
            orientation="h",
            marker_color=bar_colors,
            text=[f'%{v:.1f}' for v in df_sorted["Kar Marjı (%)"]],
            textposition="outside",
        ))
        fig.update_layout(
            title="Kar Marjı (%) — Sektör Karşılaştırması",
            height=280, **pt_merge(xaxis=dict(ticksuffix="%", gridcolor="#E2E8F0", showgrid=True, zeroline=False)),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Riskler ve fırsatlar
        col1, col2 = st.columns(2)
        with col1:
            sec("⚠️ Sektör Riskleri")
            for r in sbilgi["riskler"]:
                st.markdown(
                    f'<div style="background:#FFF7F7;border-left:3px solid #DC2626;'
                    f'border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:6px;'
                    f'color:#e8a0a0;font-size:.85rem;">⚠️ {r}</div>',
                    unsafe_allow_html=True)
        with col2:
            sec("🚀 Sektör Fırsatları")
            for f in sbilgi["firsatlar"]:
                st.markdown(
                    f'<div style="background:#F0FDF4;border-left:3px solid #059669;'
                    f'border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:6px;'
                    f'color:#065F46;font-size:.85rem;">🚀 {f}</div>',
                    unsafe_allow_html=True)

    # ════════════════════════════════
    # SEKTÖR TRENDİ
    # ════════════════════════════════
    with s3:
        sec("📈 Sektör Büyüme Trendi")

        trend = sbilgi["sektor_trendi"]
        aylar = ["Oca","Şub","Mar","Nis","May","Haz",
                 "Tem","Ağu","Eyl","Eki","Kas","Ara"]

        fig = go.Figure()
        fig.add_scatter(
            x=aylar, y=trend,
            mode="lines+markers",
            line=dict(color="#1D4ED8", width=2.5),
            marker=dict(size=7, color="#0EA5E9"),
            fill="tozeroy", fillcolor="rgba(0,102,255,0.07)",
            name=f"{tespit['sektor']} Sektörü",
        )
        # Şirketin büyüme oranını karşılaştırmalı ekle
        sirket_buyume = rapor["gelir"]["ortalama_buyume_orani"]
        fig.add_hline(
            y=sirket_buyume, line_dash="dot",
            line_color="#059669", line_width=2,
            annotation_text=f"Şirketiniz: %{sirket_buyume:.1f}",
            annotation_font_color="#059669",
        )
        fig.add_hline(
            y=np.mean(trend), line_dash="dash",
            line_color="#D97706", line_width=1.5,
            annotation_text=f"Sektör Ort: %{np.mean(trend):.1f}",
            annotation_font_color="#D97706",
        )
        fig.update_layout(
            title=f"{tespit['sektor']} Sektörü Aylık Büyüme Trendi (%)",
            height=320, **pt_merge(yaxis=dict(ticksuffix="%", gridcolor="#E2E8F0", showgrid=True, zeroline=False)),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tüm sektörleri karşılaştır
        sec("🌐 Tüm Sektör Büyümeleri")
        all_avg = {
            s: np.mean(SECTOR_DB[s]["sektor_trendi"])
            for s in SectorEngine.list_sectors()
        }
        df_all = pd.DataFrame(
            list(all_avg.items()), columns=["Sektör", "Ort. Büyüme (%)"]
        ).sort_values("Ort. Büyüme (%)", ascending=True)

        colors_all = [
            "#1D4ED8" if s == tespit["sektor"] else "#E2E8F0"
            for s in df_all["Sektör"]
        ]
        fig2 = go.Figure(go.Bar(
            x=df_all["Ort. Büyüme (%)"],
            y=df_all["Sektör"],
            orientation="h",
            marker_color=colors_all,
            text=[f'%{v:.1f}' for v in df_all["Ort. Büyüme (%)"]],
            textposition="outside",
        ))
        fig2.update_layout(
            title="Sektörel Ortalama Büyüme Karşılaştırması",
            height=380, **pt_merge(xaxis=dict(ticksuffix="%", gridcolor="#E2E8F0", showgrid=True, zeroline=False)),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ════════════════════════════════
    # DETAYLI ANALİZ
    # ════════════════════════════════
    with s4:
        sec("🔍 Sektör Detaylı Analiz")

        # Benchmark tablosu - tam detay
        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            f'border-radius:12px;padding:16px 20px;margin-bottom:16px;">'
            f'<div style="font-family:Inter,-apple-system,sans-serif;font-weight:700;'
            f'font-size:1rem;color:#0F172A;margin-bottom:8px;">'
            f'{tespit["emoji"]} {tespit["sektor"]} Sektörü — Benchmark Eşikleri</div>',
            unsafe_allow_html=True)

        bm_detail = []
        tr_names = {
            "kar_marji":"Kar Marjı","gelir_buyumesi":"Gelir Büyümesi",
            "gider_gelir_orani":"Gider/Gelir Oranı",
            "aylik_gelir":"Aylık Gelir","operasyonel_marj":"Operasyonel Marj",
        }
        for mk, mv in bm["metrik_sonuclari"].items():
            birim = mv["birim"]
            def _fv(v, b=birim):
                return fmt(v) if b=="₺" else f"%{v:.1f}"
            bm_detail.append({
                "Metrik":         tr_names.get(mk, mk),
                "Şirket Değeri":  _fv(mv["sirket_degeri"]),
                "İyi (>)":        _fv(mv["sektor_iyi"]),
                "Orta":           _fv(mv["sektor_orta"]),
                "Zayıf (<)":      _fv(mv["sektor_zayif"]),
                "Durum":          mv["durum"],
                "Skor":           f'{mv["skor"]:.0f}/100',
            })

        df_det = pd.DataFrame(bm_detail)

        def color_durum(val):
            c = {"Mükemmel":"#059669","İyi":"#3B82F6",
                 "Orta":"#D97706","Zayıf":"#DC2626"}.get(val,"")
            return f"color:{c};font-weight:600" if c else ""

        st.dataframe(
            df_det.style.map(color_durum, subset=["Durum"]),
            use_container_width=True, hide_index=True,
        )

        # Skor breakdown bar
        sec("📊 Alt Metrik Skor Dağılımı")
        alt = bm["alt_skorlar"]
        labels_tr = [tr_names.get(k,k) for k in alt]
        values    = list(alt.values())
        bar_c     = ["#059669" if v>=70 else "#D97706" if v>=40 else "#DC2626"
                     for v in values]

        fig = go.Figure(go.Bar(
            x=labels_tr, y=values,
            marker_color=bar_c,
            text=[f'{v:.0f}' for v in values],
            textposition="outside",
        ))
        fig.add_hline(y=50, line_dash="dot", line_color="#64748B",
                      annotation_text="Sektör Ortalaması")
        fig.update_layout(
            title="Sektör Benchmark Alt Skorları (0-100)",
            height=290,
            **pt_merge(yaxis=dict(range=[0,115], gridcolor="#E2E8F0", showgrid=True, zeroline=False)),
        )
        st.plotly_chart(fig, use_container_width=True)
