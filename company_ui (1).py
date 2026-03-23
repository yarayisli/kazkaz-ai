"""
KazKaz AI - Şirket Profili & Sektör Analizi Streamlit Modülü
=============================================================
app.py entegrasyonu:
    from company_ui import show_company_tab, get_profile_from_session
    with tab_profil:
        show_company_tab(fin_rapor)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from company_profile import (
    CompanyProfile, CompanyProfileEngine,
    TURKEY_MARKET_DATA, CompanySize
)

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
    dc = C_GREEN if positive else C_RED
    di = "▲" if positive else "▼"
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

def durum_renk(d):
    return {"Mükemmel":C_GREEN,"İyi":C_BLUE,"Orta":C_YELLOW,"Zayıf":C_RED}.get(d,"#8899bb")


# ─────────────────────────────────────────────
# PROFİL FORM
# ─────────────────────────────────────────────

def show_profile_form() -> CompanyProfile:
    """Şirket profili giriş formu."""
    sec("🏢 Şirket Profili")

    col1, col2, col3 = st.columns(3)

    with col1:
        sirket_adi = st.text_input(
            "Şirket Adı", 
            value=st.session_state.get("sirket_adi", "Şirketim"),
            key="cp_adi"
        )
        sektor = st.selectbox(
            "Ana Sektör",
            options=list(TURKEY_MARKET_DATA.keys()),
            index=0, key="cp_sektor"
        )
        alt_sektor = st.text_input(
            "Alt Sektör (opsiyonel)",
            placeholder="Örn: SaaS, B2B, Gıda Üretimi...",
            key="cp_alt"
        )

    with col2:
        kuruluş_yili = st.number_input(
            "Kuruluş Yılı", min_value=1900,
            max_value=datetime.now().year,
            value=2020, key="cp_yil"
        )
        calissan = st.number_input(
            "Çalışan Sayısı", min_value=1,
            max_value=100_000, value=15, key="cp_calissan"
        )
        sehir = st.selectbox(
            "Merkez Şehir",
            ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya",
             "Konya", "Adana", "Gaziantep", "Diğer"],
            key="cp_sehir"
        )

    with col3:
        sermaye = st.number_input(
            "Ödenmiş Sermaye (₺)", min_value=0,
            value=500_000, step=50_000, key="cp_sermaye"
        )
        ihracat = st.checkbox("İhracat Yapıyor", key="cp_ihracat")
        borsada = st.checkbox("Borsada İşlem Görüyor", key="cp_borsa")
        aciklama = st.text_area(
            "Şirket Açıklaması (opsiyonel)",
            placeholder="Şirketin ne yaptığını kısaca açıklayın...",
            height=80, key="cp_aciklama"
        )

    # Session state güncelle
    st.session_state["sirket_adi"] = sirket_adi

    return CompanyProfile(
        sirket_adi      = sirket_adi,
        sektor          = sektor,
        alt_sektor      = alt_sektor,
        kuruluş_yili    = kuruluş_yili,
        calissan_sayisi = calissan,
        sehir           = sehir,
        sermaye         = sermaye,
        ihracat_yapıyor = ihracat,
        borsada_mi      = borsada,
        aciklama        = aciklama,
    )


# ─────────────────────────────────────────────
# ANA SEKME
# ─────────────────────────────────────────────

def show_company_tab(fin_rapor: dict):
    """Şirket profili ana sekmesi."""

    st.markdown(
        '<div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#00d4ff,#0066ff);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '🏢 Şirket Profili & Piyasa Analizi</div>'
        '<div style="color:#4a6fa5;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'Profil · Sektöre Özel KPI · BIST Karşılaştırması · Rakip Analizi</div>',
        unsafe_allow_html=True)

    # ── Profil Formu ──
    profile = show_profile_form()

    if st.button("🔍 Analizi Güncelle", use_container_width=True, key="cp_analyze"):
        with st.spinner("Sektör analizi yapılıyor..."):
            try:
                engine = CompanyProfileEngine(profile, fin_rapor)
                st.session_state["cp_rapor"]   = engine.full_report()
                st.session_state["cp_profile"] = profile
            except Exception as e:
                st.error(f"Analiz hatası: {e}")
        st.rerun()

    # İlk kez otomatik hesapla
    if "cp_rapor" not in st.session_state:
        with st.spinner("İlk analiz yapılıyor..."):
            try:
                engine = CompanyProfileEngine(profile, fin_rapor)
                st.session_state["cp_rapor"]   = engine.full_report()
                st.session_state["cp_profile"] = profile
            except Exception as e:
                st.error(f"Hata: {e}")
                return

    cp     = st.session_state["cp_rapor"]
    profil = cp["profil"]
    market = cp["market_data"]

    st.markdown("---")

    # ── Alt Sekmeler ──
    s1, s2, s3, s4 = st.tabs([
        "📋 Şirket Kartı",
        "📊 Sektöre Özel KPI'lar",
        "🏆 Rakip Analizi",
        "📈 BIST & Piyasa",
    ])

    # ════════════ ŞİRKET KARTI ════════════
    with s1:
        # Özet kart
        yas = profil["yas"]
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0f1629,#1a2540);'
            f'border:1px solid #1e3a5f;border-radius:20px;padding:28px 32px;'
            f'margin-bottom:20px;">'
            f'<div style="display:flex;align-items:center;gap:20px;margin-bottom:20px;">'
            f'<div style="width:64px;height:64px;background:linear-gradient(135deg,#0066ff,#7c3aed);'
            f'border-radius:16px;display:flex;align-items:center;justify-content:center;'
            f'font-size:2rem;">🏢</div>'
            f'<div>'
            f'<div style="font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;'
            f'color:#e8eaf0;">{profil["sirket_adi"]}</div>'
            f'<div style="color:#4a6fa5;font-size:.85rem;">'
            f'{profil["sektor"]} · {profil["sehir"]}</div>'
            f'</div></div>'
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">'
            f'<div style="background:#0a0e1a;border-radius:12px;padding:14px;">'
            f'<div style="color:#4a6fa5;font-size:.7rem;text-transform:uppercase;'
            f'letter-spacing:1px;">Kuruluş</div>'
            f'<div style="color:#e8eaf0;font-weight:700;">{profil["kuruluş_yili"]}</div>'
            f'<div style="color:#4a6fa5;font-size:.75rem;">{yas} yıl önce</div>'
            f'</div>'
            f'<div style="background:#0a0e1a;border-radius:12px;padding:14px;">'
            f'<div style="color:#4a6fa5;font-size:.7rem;text-transform:uppercase;'
            f'letter-spacing:1px;">Çalışan</div>'
            f'<div style="color:#e8eaf0;font-weight:700;">{profil["calissan_sayisi"]}</div>'
            f'<div style="color:#4a6fa5;font-size:.75rem;">{profil["buyukluk"]}</div>'
            f'</div>'
            f'<div style="background:#0a0e1a;border-radius:12px;padding:14px;">'
            f'<div style="color:#4a6fa5;font-size:.7rem;text-transform:uppercase;'
            f'letter-spacing:1px;">Segment</div>'
            f'<div style="color:#60a5fa;font-weight:700;">'
            f'{profil["buyukluk"].split("(")[0].strip()}</div>'
            f'<div style="color:#4a6fa5;font-size:.75rem;">{profil["sektor"]}</div>'
            f'</div>'
            f'<div style="background:#0a0e1a;border-radius:12px;padding:14px;">'
            f'<div style="color:#4a6fa5;font-size:.7rem;text-transform:uppercase;'
            f'letter-spacing:1px;">Özellik</div>'
            f'<div style="color:#e8eaf0;font-weight:700;">'
            f'{"🌍 İhracatçı" if profil["ihracat"] else "🇹🇷 Yerel"}</div>'
            f'<div style="color:#4a6fa5;font-size:.75rem;">'
            f'{"📈 BIST" if profil["borsada"] else "🔒 Özel"}</div>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True)

        # Piyasa bilgileri
        sec("📊 Sektör Piyasa Bilgileri")
        c1,c2,c3,c4 = st.columns(4)
        with c1: kpi("2024 Sektör Büyümesi",
                     market.get("sektör_buyume_2024","-"), color=C_GREEN)
        with c2: kpi("Enflasyon Üzeri",
                     market.get("enflasyon_uzeri_buyume","-"),
                     color=C_GREEN if "+" in str(market.get("enflasyon_uzeri_buyume","")) else C_RED)
        with c3: kpi("Ort. F/K Oranı",
                     str(market.get("ortalama_fiyat_kazanc","-")), color=C_BLUE)
        with c4: kpi("Vergi Avantajı",
                     "✅ Var" if market.get("vergi_avantaji") else "❌ Yok",
                     color=C_GREEN)

        # Vergi avantajı detayı
        if market.get("vergi_avantaji"):
            st.markdown(
                f'<div style="background:#0a1a10;border-left:3px solid {C_GREEN};'
                f'border-radius:0 10px 10px 0;padding:10px 14px;margin-top:8px;">'
                f'<div style="color:#4a6fa5;font-size:.75rem;margin-bottom:3px;">'
                f'💰 Vergi & Teşvik Avantajları</div>'
                f'<div style="color:#a0e8c0;font-size:.85rem;">'
                f'{market["vergi_avantaji"]}</div></div>',
                unsafe_allow_html=True)

    # ════════════ SEKTÖRE ÖZEL KPI'LAR ════════════
    with s2:
        sec(f"📊 {profil['sektor']} Sektörü KPI Analizi")

        kpiler = cp["kpiler"]
        if not kpiler:
            st.info("KPI hesaplamak için finansal veri yükleyin.")
            return

        # KPI kartları
        kpi_listesi = list(kpiler.items())
        cols = st.columns(min(len(kpi_listesi), 3))

        for i, (kpi_adi, kpi_data) in enumerate(kpi_listesi):
            with cols[i % 3]:
                deger    = kpi_data.get("deger", 0)
                hedef    = kpi_data.get("hedef", 0)
                birim    = kpi_data.get("birim", "")
                durum    = kpi_data.get("durum", "Orta")
                perf_pct = kpi_data.get("performans_pct", 50)
                renk     = durum_renk(durum)

                # Değer formatlama
                if birim == "₺/yıl" or birim == "₺":
                    deger_str = fmt(deger)
                    hedef_str = fmt(hedef)
                else:
                    deger_str = f"{deger:,.1f} {birim}"
                    hedef_str = f"{hedef} {birim}"

                st.markdown(
                    f'<div style="background:#111827;border:1px solid #1e3a5f;'
                    f'border-radius:14px;padding:16px;margin-bottom:10px;">'
                    f'<div style="font-size:.72rem;color:#4a6fa5;letter-spacing:1px;'
                    f'text-transform:uppercase;margin-bottom:6px;">{kpi_adi}</div>'
                    f'<div style="font-family:Syne,sans-serif;font-size:1.3rem;'
                    f'font-weight:700;color:{renk};margin-bottom:4px;">{deger_str}</div>'
                    f'<div style="color:#4a6fa5;font-size:.75rem;margin-bottom:8px;">'
                    f'Hedef: {hedef_str}</div>'
                    f'<div style="background:#1e3a5f;border-radius:4px;height:6px;'
                    f'overflow:hidden;">'
                    f'<div style="background:{renk};width:{min(perf_pct,100)}%;'
                    f'height:100%;border-radius:4px;"></div></div>'
                    f'<div style="color:{renk};font-size:.72rem;margin-top:4px;">'
                    f'{durum} — %{perf_pct:.0f}</div>'
                    f'</div>',
                    unsafe_allow_html=True)

        # KPI tablo özeti
        sec("📋 KPI Özet Tablosu")
        kpi_df = pd.DataFrame([
            {
                "KPI":      k,
                "Değer":    f'{v.get("deger",0):,.1f} {v.get("birim","")}',
                "Hedef":    f'{v.get("hedef",0)} {v.get("birim","")}',
                "Perf. %":  v.get("performans_pct", 0),
                "Durum":    v.get("durum", "-"),
            }
            for k, v in kpiler.items()
        ])
        def color_d(val):
            c = {"Mükemmel":C_GREEN,"İyi":C_BLUE,
                 "Orta":C_YELLOW,"Zayıf":C_RED}.get(val,"")
            return f"color:{c};font-weight:600" if c else ""

        st.dataframe(
            kpi_df.style.applymap(color_d, subset=["Durum"])
                        .format({"Perf. %": "{:.0f}%"}),
            use_container_width=True, hide_index=True)

        # Sektörün hedef KPI'ları
        market_kpiler = market.get("kpiler", {})
        if market_kpiler:
            sec(f"🎯 {profil['sektor']} Sektörü Tüm Hedef KPI'lar")
            hedef_df = pd.DataFrame([
                {"KPI": k, "Sektör Hedefi": f'{v["hedef"]} {v["birim"]}'}
                for k, v in market_kpiler.items()
            ])
            st.dataframe(hedef_df, use_container_width=True, hide_index=True)

    # ════════════ RAKİP ANALİZİ ════════════
    with s3:
        sec(f"🏆 {profil['buyukluk'].split('(')[0].strip()} Segment Rakip Analizi")

        rakip_df = cp["rakip_tablosu"]
        toplam = cp["toplam_rakip"]

        # Sıralama — tüm hesaplamalar güvenli
        raw_sira = cp.get("sirket_sirasi", toplam + 1)
        try:
            sirket_sirasi = int(float(str(raw_sira)))
        except Exception:
            sirket_sirasi = toplam + 1

        toplam_n   = max(int(toplam), 1)
        yuzdelik   = float(round((1 - sirket_sirasi / (toplam_n + 1)) * 100, 0))
        y_renk     = C_GREEN if yuzdelik >= 60 else C_YELLOW if yuzdelik >= 40 else C_RED
        ust_yarida = sirket_sirasi <= (toplam_n // 2 + 1)

        c1,c2,c3 = st.columns(3)
        with c1:
            kpi("Segment Rakip Sayısı", str(toplam_n),
                f'{profil["sektor"]} segmenti')
        with c2:
            kpi("Kar Marjı Sıralaması",
                f'{sirket_sirasi}. / {toplam_n+1}',
                "Rakipler arasında",
                color=y_renk, positive=ust_yarida)
        with c3:
            kpi("Yüzdelik Dilim", f'%{int(yuzdelik)}',
                "Üst % daha iyi", color=y_renk, positive=yuzdelik>=50)

        # Tablo
        sec("📋 Detaylı Rakip Tablosu")

        def highlight(row):
            if "★" in str(row["Şirket"]):
                return ["background-color:#0a1e3a;color:#60d4ff;font-weight:bold"] * len(row)
            return [""] * len(row)

        display_df = rakip_df.drop(columns=["Kaynak"], errors="ignore")
        st.dataframe(
            display_df.style.apply(highlight, axis=1)
                            .format({
                                "Kar Marjı (%)":      "{:.1f}%",
                                "Büyüme (%)":         "{:.1f}%",
                                "Gider/Gelir (%)":    "{:.1f}%",
                                "Çalışan/Gelir (K₺)": "{:.0f}K ₺",
                            }),
            use_container_width=True, hide_index=True)

        # Bar grafik
        sec("📊 Kar Marjı Karşılaştırması")
        sorted_df = rakip_df.sort_values("Kar Marjı (%)", ascending=True)
        bar_colors = [
            C_BLUE if "★" in str(s) else "#1e3a5f"
            for s in sorted_df["Şirket"]
        ]
        fig = go.Figure(go.Bar(
            x=sorted_df["Kar Marjı (%)"],
            y=sorted_df["Şirket"],
            orientation="h",
            marker_color=bar_colors,
            text=[f'%{v:.1f}' for v in sorted_df["Kar Marjı (%)"]],
            textposition="outside",
        ))
        fig.update_layout(
            title=f"Kar Marjı — {profil['sektor']} {profil['buyukluk'].split('(')[0].strip()} Segment",
            height=max(280, len(sorted_df) * 45),
            **{k:v for k,v in PT.items() if k != 'xaxis'},
            xaxis=dict(ticksuffix="%", gridcolor="#1e2d4a",
                       showgrid=True, zeroline=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ════════════ BIST & PİYASA ════════════
    with s4:
        sec("📈 BIST & Türkiye Piyasa Verileri")

        bist_list = cp["bist_sektorleri"]

        # BIST sektör oyuncuları
        if bist_list:
            st.markdown(
                f'<div style="background:#0d1520;border:1px solid #1e3a5f;'
                f'border-radius:12px;padding:16px 20px;margin-bottom:16px;">'
                f'<div style="color:#4a6fa5;font-size:.75rem;text-transform:uppercase;'
                f'letter-spacing:1px;margin-bottom:10px;">'
                f'📊 {profil["sektor"]} Sektörü BIST Oyuncuları</div>'
                + "".join([
                    f'<span style="background:#1e3a5f;color:#60a5fa;'
                    f'padding:4px 10px;border-radius:20px;font-size:.8rem;'
                    f'margin:3px 3px;display:inline-block;">{b}</span>'
                    for b in bist_list
                ]) +
                f'</div>', unsafe_allow_html=True)

        # Piyasa karşılaştırması
        sec("📊 Şirketiniz vs Piyasa Ortalaması")

        g = fin_rapor.get("gelir", {})
        k = fin_rapor.get("karlilik", {})
        bm = TURKEY_MARKET_DATA.get(profil["sektor"], {})

        # Gerçek sektör büyüme rakamını parse et
        buyume_str = bm.get("sektör_buyume_2024", "%0")
        try:
            sektor_buyume = float(buyume_str.replace("%","").replace("+",""))
        except:
            sektor_buyume = 10.0

        karsilastirma = [
            {
                "Metrik":        "Kar Marjı (%)",
                "Şirketiniz":    k.get("kar_marji", 0),
                "Sektör Hedef":  12.0,
                "BIST Ort.":     8.5,
            },
            {
                "Metrik":        "Büyüme (%)",
                "Şirketiniz":    g.get("ortalama_buyume_orani", 0),
                "Sektör Hedef":  sektor_buyume / 12,
                "BIST Ort.":     5.0,
            },
        ]
        df_kars = pd.DataFrame(karsilastirma)

        fig = go.Figure()
        for col, color in [
            ("Şirketiniz", C_BLUE),
            ("Sektör Hedef", C_GREEN),
            ("BIST Ort.", C_YELLOW),
        ]:
            fig.add_bar(
                name=col,
                x=df_kars["Metrik"],
                y=df_kars[col],
                marker_color=color,
                opacity=0.85,
            )
        fig.update_layout(
            barmode="group",
            title="Şirket vs Sektör vs BIST Karşılaştırması",
            height=300, **PT,
            legend=dict(orientation="h", y=1.12, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Enflasyon bağlamı
        sec("💡 Piyasa Bağlamı")
        enf_uzeri = bm.get("enflasyon_uzeri_buyume", "0%")
        pozitif   = "+" in str(enf_uzeri) or (
            "-" not in str(enf_uzeri) and "0" not in str(enf_uzeri))

        bilgiler = [
            ("2024 Sektör Büyümesi", bm.get("sektör_buyume_2024","-"), True),
            ("Enflasyon Üzeri Reel Büyüme", enf_uzeri, pozitif),
            ("Ortalama F/K Çarpanı", str(bm.get("ortalama_fiyat_kazanc","-")), True),
            ("Vergi & Teşvik", bm.get("vergi_avantaji","Yok"), bool(bm.get("vergi_avantaji"))),
        ]
        for baslik, deger, iyi in bilgiler:
            renk = C_GREEN if iyi else C_RED
            st.markdown(
                f'<div style="background:#111827;border-left:3px solid {renk};'
                f'border-radius:0 10px 10px 0;padding:10px 16px;margin-bottom:6px;'
                f'display:flex;justify-content:space-between;">'
                f'<span style="color:#8aabcc;font-size:.85rem;">{baslik}</span>'
                f'<span style="color:{renk};font-weight:700;font-size:.88rem;">'
                f'{deger}</span></div>',
                unsafe_allow_html=True)


def get_profile_from_session() -> dict:
    """Session state'ten mevcut profili döndürür."""
    if "cp_profile" in st.session_state:
        return st.session_state["cp_profile"].to_dict()
    return {}
