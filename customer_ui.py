"""
KazKaz AI - Müşteri & Ürün Analizi Streamlit Modülü
====================================================
app.py entegrasyonu:
    from customer_ui import show_customer_tab
    with tab_musteri:
        show_customer_tab(df)
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


from customer_engine import CustomerEngine

# ─────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────


def show_customer_tab(df: pd.DataFrame):
    """Müşteri & ürün analizi ana sekmesi."""

    st.markdown(
        '<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#0EA5E9,#1D4ED8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '👥 Müşteri & Ürün Analizi</div>'
        '<div style="color:#64748B;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'Gelir · Karlılık · RFM Segmentasyon · Churn Risk</div>',
        unsafe_allow_html=True)

    # Motor başlat
    try:
        engine = CustomerEngine(df)
        rapor  = engine.full_report()
    except Exception as e:
        st.error(f"Müşteri analizi hatası: {e}")
        return

    # Müşteri/ürün verisi yoksa yönlendir
    if not rapor["has_customers"]:
        _show_no_data_guide()
        return

    # ── Özet KPI ──
    mo = rapor["musteri_ozet"]
    uo = rapor["urun_ozet"]
    co = rapor["churn_ozet"]

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Toplam Müşteri",   str(mo.get("toplam_musteri",0)),   color=C_BLUE)
    with c2: kpi("Toplam Ürün",      str(uo.get("toplam_urun",0)),      color=C_CYAN)
    with c3: kpi("Churn Riski Yük.", str(co.get("yuksek_risk",0)),
                 color=C_RED if co.get("yuksek_risk",0)>0 else C_GREEN,
                 positive=bool(int(co.get("yuksek_risk") or 0) == 0))
    with c4: kpi("En İyi Müşteri",   mo.get("top3_musteri",["-"])[0] if mo.get("top3_musteri") else "-",
                 color=C_GREEN)
    with c5: kpi("En İyi Ürün",      uo.get("en_iyi_urun","-"),         color=C_GREEN)

    # Konsantrasyon uyarısı
    konc = rapor["konsantrasyon"]
    if konc.get("konsantrasyon_riski"):
        st.markdown(
            f'<div style="background:#FFF7F7;border:1px solid #DC262644;'
            f'border-radius:10px;padding:12px 16px;margin:8px 0;color:#ff8080;'
            f'font-size:.86rem;">⚠️ <b>Müşteri Konsantrasyonu Riski:</b> '
            f'En büyük %20 müşteriniz toplam gelirin '
            f'<b>%{konc.get("top20_pct_pay",0)}</b>'
            f'ini oluşturuyor. Bu müşterilerin kaybı büyük risk yaratır.</div>',
            unsafe_allow_html=True)

    st.markdown("---")

    # ── Alt Sekmeler ──
    s1, s2, s3, s4, s5 = st.tabs([
        "💰 Müşteri Gelirleri",
        "📦 Ürün Analizi",
        "📊 Karlılık",
        "🎯 RFM Segmentasyon",
        "⚠️ Churn Riski",
    ])

    # ════════ MÜŞTERİ GELİRLERİ ════════
    with s1:
        sec("💰 Müşteri Bazında Gelir Sıralaması")
        musteri_df = rapor["musteri_gelir"]

        if musteri_df.empty:
            st.info("Müşteri bazında veri bulunamadı.")
        else:
            # Yatay bar chart — top 15
            top15 = musteri_df.head(15)
            fig = go.Figure(go.Bar(
                x=top15["Toplam Gelir (₺)"],
                y=top15["Müşteri"],
                orientation="h",
                marker=dict(
                    color=top15["Toplam Gelir (₺)"],
                    colorscale=[[0,"#E2E8F0"],[1,C_BLUE]],
                ),
                text=[fmt(v) for v in top15["Toplam Gelir (₺)"]],
                textposition="outside",
            ))
            fig.update_layout(
                title="En Değerli Müşteriler (Top 15)",
                height=max(300, len(top15)*40),
                yaxis=dict(autorange="reversed",
                           gridcolor="#E2E8F0", showgrid=True, zeroline=False),
                **{k:v for k,v in PLOTLY_THEME.items() if k!="yaxis"},
            )
            st.plotly_chart(fig, use_container_width=True)

            # Pareto grafiği
            sec("📊 Pareto Analizi (80/20 Kuralı)")
            pareto = konc.get("pareto_df", pd.DataFrame())
            if not pareto.empty:
                fig2 = go.Figure()
                fig2.add_bar(
                    x=pareto["Müşteri"],
                    y=pareto["Toplam Gelir (₺)"],
                    name="Gelir", marker_color=C_BLUE, opacity=.85,
                )
                fig2.add_scatter(
                    x=pareto["Müşteri"],
                    y=pareto["Kümülatif Pay (%)"],
                    name="Kümülatif %", yaxis="y2",
                    mode="lines+markers",
                    line=dict(color=C_YELLOW, width=2),
                    marker=dict(size=5),
                )
                fig2.add_hline(
                    y=80, line_dash="dash",
                    line_color=C_RED, opacity=.6,
                    annotation_text="%80 eşiği",
                    annotation_font_color=C_RED,
                    yref="y2",
                )
                fig2.update_layout(
                    height=300,
                    yaxis2=dict(overlaying="y", side="right",
                                range=[0,110], ticksuffix="%",
                                gridcolor="#E2E8F0"),
                    legend=dict(orientation="h", y=1.1, x=0),
                    **PLOTLY_THEME,
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Tablo
            sec("📋 Müşteri Gelir Tablosu")
            st.dataframe(
                musteri_df.style.format({
                    "Toplam Gelir (₺)": "{:,.0f} ₺",
                    "Ort. İşlem (₺)":   "{:,.0f} ₺",
                }),
                use_container_width=True, hide_index=True)

    # ════════ ÜRÜN ANALİZİ ════════
    with s2:
        sec("📦 Ürün / Hizmet Bazında Gelir")
        urun_df = rapor["urun_gelir"]

        if urun_df.empty:
            st.info("Ürün bazında veri bulunamadı.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                # Bar chart
                fig = go.Figure(go.Bar(
                    x=urun_df["Toplam Gelir (₺)"],
                    y=urun_df["Ürün"],
                    orientation="h",
                    marker=dict(
                        color=urun_df["Toplam Gelir (₺)"],
                        colorscale=[[0,"#E2E8F0"],[1,C_CYAN]],
                    ),
                    text=[fmt(v) for v in urun_df["Toplam Gelir (₺)"]],
                    textposition="outside",
                ))
                fig.update_layout(
                    title="Ürün Bazında Gelir",
                    height=max(280, len(urun_df)*45),
                    yaxis=dict(autorange="reversed",
                               gridcolor="#E2E8F0", showgrid=True, zeroline=False),
                    **{k:v for k,v in PLOTLY_THEME.items() if k!="yaxis"},
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Pasta
                fig2 = px.pie(
                    urun_df, values="Toplam Gelir (₺)", names="Ürün",
                    color_discrete_sequence=[
                        C_BLUE, C_CYAN, C_GREEN, C_YELLOW,
                        C_PURPLE, "#f97316", "#06b6d4", "#84cc16"],
                    hole=0.5,
                )
                fig2.update_layout(title="Gelir Dağılımı", height=280, **PLOTLY_THEME)
                st.plotly_chart(fig2, use_container_width=True)

            sec("📋 Ürün Detay Tablosu")
            st.dataframe(
                urun_df.style.format({
                    "Toplam Gelir (₺)": "{:,.0f} ₺",
                    "Ort. Fiyat (₺)":   "{:,.0f} ₺",
                }),
                use_container_width=True, hide_index=True)

    # ════════ KARLILIK ════════
    with s3:
        col1, col2 = st.columns(2)

        with col1:
            sec("👥 Müşteri Karlılığı")
            musteri_kar = rapor["musteri_kar"]
            if not musteri_kar.empty:
                colors_m = [C_GREEN if v >= 0 else C_RED
                            for v in musteri_kar["Net Kar (₺)"]]
                fig = go.Figure(go.Bar(
                    x=musteri_kar["Müşteri"],
                    y=musteri_kar["Net Kar (₺)"],
                    marker_color=colors_m,
                    text=[fmt(v) for v in musteri_kar["Net Kar (₺)"]],
                    textposition="outside",
                ))
                fig.add_hline(y=0, line_dash="dash",
                              line_color=C_RED, opacity=.5)
                fig.update_layout(
                    title="Müşteri Bazında Net Kar",
                    height=280, **PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(
                    musteri_kar.style.format({
                        "Gelir (₺)":         "{:,.0f} ₺",
                        "Tahmini Gider (₺)":  "{:,.0f} ₺",
                        "Net Kar (₺)":        "{:,.0f} ₺",
                        "Kar Marjı (%)":      "{:.1f}%",
                    }).applymap(
                        lambda v: "color:#059669" if isinstance(v,(int,float)) and v>0
                                  else "color:#DC2626" if isinstance(v,(int,float)) and v<0
                                  else "",
                        subset=["Net Kar (₺)"]
                    ),
                    use_container_width=True, hide_index=True)

        with col2:
            sec("📦 Ürün Katkı Marjı")
            urun_kar = rapor["urun_kar"]
            if not urun_kar.empty:
                colors_u = [C_GREEN if v >= 0 else C_RED
                            for v in urun_kar["Katkı Marjı (%)"]]
                fig2 = go.Figure(go.Bar(
                    x=urun_kar["Ürün/Hizmet"],
                    y=urun_kar["Katkı Marjı (%)"],
                    marker_color=colors_u,
                    text=[f'%{v:.1f}' for v in urun_kar["Katkı Marjı (%)"]],
                    textposition="outside",
                ))
                fig2.update_layout(
                    title="Ürün Katkı Marjı (%)",
                    height=280,
                    yaxis=dict(ticksuffix="%",
                               gridcolor="#E2E8F0", showgrid=True, zeroline=False),
                    **{k:v for k,v in PLOTLY_THEME.items() if k!="yaxis"},
                )
                st.plotly_chart(fig2, use_container_width=True)

                st.dataframe(
                    urun_kar.style.format({
                        "Gelir (₺)":         "{:,.0f} ₺",
                        "Tahmini Gider (₺)":  "{:,.0f} ₺",
                        "Katkı Marjı (₺)":    "{:,.0f} ₺",
                        "Katkı Marjı (%)":    "{:.1f}%",
                    }),
                    use_container_width=True, hide_index=True)

    # ════════ RFM SEGMENTASYON ════════
    with s4:
        sec("🎯 RFM Müşteri Segmentasyonu")
        st.markdown(
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            'border-radius:10px;padding:12px 16px;margin-bottom:14px;">'
            '<div style="color:#1D4ED8;font-size:.82rem;font-weight:600;'
            'margin-bottom:6px;">RFM Nedir?</div>'
            '<div style="color:#64748B;font-size:.8rem;line-height:1.6;">'
            '📅 <b>Recency</b>: Son alışveriş ne kadar yakın? (Yakın = iyi)<br>'
            '🔄 <b>Frequency</b>: Ne sıklıkla alışveriş yapıyor? (Sık = iyi)<br>'
            '💰 <b>Monetary</b>: Ne kadar harcıyor? (Fazla = iyi)'
            '</div></div>',
            unsafe_allow_html=True)

        rfm_df    = rapor["rfm"]
        seg_df    = rapor["rfm_segment"]

        if rfm_df.empty:
            st.info("RFM analizi için en az 2 farklı müşteri ve işlem gereklidir.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                sec("📊 Segment Dağılımı")
                if not seg_df.empty:
                    fig = px.pie(
                        seg_df,
                        values="Müşteri Sayısı",
                        names="Segment",
                        color_discrete_sequence=[
                            C_GREEN, C_BLUE, C_CYAN,
                            C_YELLOW, C_RED, C_PURPLE, "#f97316"],
                        hole=0.4,
                    )
                    fig.update_layout(height=280, **PLOTLY_THEME)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                sec("💰 Segment Gelir Karşılaştırması")
                if not seg_df.empty:
                    fig2 = go.Figure(go.Bar(
                        x=seg_df["Segment"],
                        y=seg_df["Toplam Gelir (₺)"],
                        marker=dict(
                            color=seg_df["Toplam Gelir (₺)"],
                            colorscale=[[0,"#E2E8F0"],[1,C_GREEN]],
                        ),
                        text=[fmt(v) for v in seg_df["Toplam Gelir (₺)"]],
                        textposition="outside",
                    ))
                    fig2.update_layout(
                        title="Segment Bazında Toplam Gelir",
                        height=280, **PLOTLY_THEME)
                    st.plotly_chart(fig2, use_container_width=True)

            sec("📋 Segment Özet Tablosu")
            st.dataframe(
                seg_df.style.format({
                    "Ort. Gelir (₺)":     "{:,.0f} ₺",
                    "Toplam Gelir (₺)":   "{:,.0f} ₺",
                }),
                use_container_width=True, hide_index=True)

            sec("📋 Müşteri RFM Detayı")
            display_rfm = rfm_df[[
                "Müşteri","Recency","Frequency","Monetary",
                "R_Score","F_Score","M_Score","RFM_Score","Segment"
            ]].copy()
            display_rfm["Monetary"] = display_rfm["Monetary"].apply(fmt)
            st.dataframe(display_rfm, use_container_width=True, hide_index=True)

    # ════════ CHURN RİSKİ ════════
    with s5:
        sec("⚠️ Churn Risk Analizi")

        risk_ozet = co
        _yuksek = int(risk_ozet.get("yuksek_risk") or 0)
        _orta   = int(risk_ozet.get("orta_risk") or 0)
        _rgelir = float(risk_ozet.get("risk_gelir") or 0)
        c1,c2,c3 = st.columns(3)
        with c1:
            kpi("Yüksek Riskli", str(_yuksek), delta="Acil aksiyon", color=C_RED, positive=bool(_yuksek == 0))
        with c2:
            kpi("Orta Riskli", str(_orta), delta="Takip et", color=C_YELLOW, positive=False)
        with c3:
            kpi("Risk Altındaki Gelir", fmt(_rgelir), delta="Yüksek risk segmenti", color=C_RED, positive=bool(_rgelir == 0))

        churn_df = rapor["churn_risk"]
        if churn_df.empty:
            st.info("Churn analizi için çoklu dönem verisi gereklidir.")
        else:
            # Yüksek risk öne al
            col1, col2 = st.columns(2)

            with col1:
                sec("🔴 Yüksek Riskli Müşteriler")
                yuksek = churn_df[churn_df["Risk Seviyesi"] == "🔴 Yüksek"]
                if yuksek.empty:
                    st.success("✅ Yüksek riskli müşteri yok!")
                else:
                    for _, row in yuksek.iterrows():
                        st.markdown(
                            f'<div style="background:#FFF7F7;border-left:4px solid {C_RED};'
                            f'border-radius:0 10px 10px 0;padding:12px 16px;'
                            f'margin-bottom:8px;">'
                            f'<div style="color:{C_RED};font-weight:700;font-size:.88rem;">'
                            f'{row["Müşteri"]}</div>'
                            f'<div style="color:#4B5563;font-size:.8rem;margin-top:4px;">'
                            f'Son işlem: {row["Son İşlem"]} · '
                            f'{row["Geçen Gün"]} gün geçti · '
                            f'Risk: %{row["Risk Skoru (%)"]}</div>'
                            f'<div style="color:{C_YELLOW};font-size:.78rem;margin-top:3px;">'
                            f'💰 Toplam gelir: {fmt(row["Toplam Gelir (₺)"])}</div>'
                            f'</div>',
                            unsafe_allow_html=True)

            with col2:
                sec("📊 Risk Dağılımı")
                risk_counts = churn_df["Risk Seviyesi"].value_counts().reset_index()
                risk_counts.columns = ["Risk", "Sayı"]
                fig = px.pie(
                    risk_counts, values="Sayı", names="Risk",
                    color_discrete_map={
                        "🔴 Yüksek": C_RED,
                        "🟡 Orta":   C_YELLOW,
                        "🟢 Düşük":  C_GREEN,
                    },
                    hole=0.5,
                )
                fig.update_layout(height=280, **PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)

            sec("📋 Tüm Müşteri Risk Tablosu")
            st.dataframe(
                churn_df.style.format({
                    "Toplam Gelir (₺)": "{:,.0f} ₺",
                }).applymap(
                    lambda v: "color:#DC2626;font-weight:600"
                    if v == "🔴 Yüksek" else
                    "color:#D97706" if v == "🟡 Orta" else
                    "color:#059669" if v == "🟢 Düşük" else "",
                    subset=["Risk Seviyesi"]
                ),
                use_container_width=True, hide_index=True)


def _show_no_data_guide():
    """Müşteri verisi yoksa nasıl ekleneceğini göster."""
    st.markdown(
        '<div style="background:#F8FAFC;border:1px solid #BFDBFE;'
        'border-radius:14px;padding:24px;margin-bottom:20px;">'
        '<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.1rem;'
        'font-weight:700;color:#1D4ED8;margin-bottom:12px;">'
        '📋 Müşteri & Ürün Analizi Nasıl Aktifleştirilir?</div>'
        '<div style="color:#4B5563;font-size:.88rem;line-height:1.8;">'
        'Mevcut CSV/Excel dosyanıza 2 sütun ekleyin:'
        '</div></div>',
        unsafe_allow_html=True)

    from customer_engine import CustomerEngine
    ornek = CustomerEngine.ornek_veri()
    st.dataframe(ornek, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇ Örnek CSV İndir (Müşteri & Ürün sütunlu)",
        ornek.to_csv(index=False).encode("utf-8"),
        "ornek_musteri_urun.csv",
        "text/csv",
        use_container_width=True,
    )

    st.markdown("""
    **Adımlar:**
    1. Örnek CSV'yi indirin
    2. Kendi verilerinizi aynı formatta düzenleyin
    3. Sol panelden yeni CSV'yi yükleyin
    4. Bu sekme otomatik dolacak
    """)
