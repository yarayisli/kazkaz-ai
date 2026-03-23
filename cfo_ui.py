"""
KazKaz AI - CFO AI Agent Streamlit Modülü (v15)
================================================
app.py entegrasyonu:
    from cfo_ui import show_cfo_tab
    with tab_cfo:
        show_cfo_tab(fin_rapor, sirket_adi, ai_engine, cf_rapor, debt_rapor)
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from cfo_agent import (
    CFOAgent, AlertLevel, Alert,
    FinancialHealthTool, InvestmentAdvisorTool, DebtAdvisorTool
)

# ─────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────

C_GREEN  = "#10d994"
C_RED    = "#ff4757"
C_YELLOW = "#fbbf24"
C_BLUE   = "#0066ff"
C_CYAN   = "#00d4ff"
C_PURPLE = "#7c3aed"

def fmt(v):
    if abs(v) >= 1_000_000: return f"{v/1_000_000:.1f}M ₺"
    if abs(v) >= 1_000:     return f"{v/1_000:.0f}K ₺"
    return f"{v:,.0f} ₺"

def alert_color(seviye: AlertLevel) -> str:
    return {
        AlertLevel.KRITIK:  C_RED,
        AlertLevel.DIKKAT:  C_YELLOW,
        AlertLevel.BILGI:   C_BLUE,
        AlertLevel.POZITIF: C_GREEN,
    }.get(seviye, "#8899bb")

def alert_bg(seviye: AlertLevel) -> str:
    return {
        AlertLevel.KRITIK:  "#1a0a0a",
        AlertLevel.DIKKAT:  "#1a1500",
        AlertLevel.BILGI:   "#0a0f1a",
        AlertLevel.POZITIF: "#0a1a0f",
    }.get(seviye, "#111827")

def sec(text):
    st.markdown(
        f'<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;'
        f'color:#e8eaf0;padding:6px 0 10px;border-bottom:1px solid #1e2d4a;'
        f'margin:16px 0 14px;">{text}</div>', unsafe_allow_html=True)

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


# ─────────────────────────────────────────────
# ANA CFO SEKME
# ─────────────────────────────────────────────

def show_cfo_tab(
    fin_rapor:  dict,
    sirket_adi: str  = "Şirket",
    ai_engine        = None,
    cf_rapor:   dict = None,
    debt_rapor: dict = None,
):
    st.markdown(
        '<div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#00d4ff,#0066ff,#7c3aed);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '🧠 CFO AI Agent</div>'
        '<div style="color:#4a6fa5;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'Proaktif Analiz · Uyarılar · Yatırım & Borç Önerileri · Otomatik Rapor</div>',
        unsafe_allow_html=True)

    if ai_engine is None:
        st.markdown(
            '<div style="background:#0d1520;border:1px solid #ff475744;'
            'border-radius:12px;padding:20px;text-align:center;color:#ff8080;">'
            '🔒 CFO Agent için AI motoru gerekli.<br>'
            '<span style="font-size:.85rem;color:#4a6fa5;">'
            'Sol panelden Groq veya Gemini API anahtarınızı ekleyin.</span></div>',
            unsafe_allow_html=True)
        return

    # ── Agent oluştur / cache ──
    agent_key = f"cfo_agent_{sirket_adi}"
    if agent_key not in st.session_state:
        with st.spinner("CFO Agent başlatılıyor..."):
            try:
                agent = CFOAgent(
                    ai_engine  = ai_engine,
                    fin_rapor  = fin_rapor,
                    sirket_adi = sirket_adi,
                    cf_rapor   = cf_rapor,
                    debt_rapor = debt_rapor,
                )
                agent.analyze()
                st.session_state[agent_key] = agent
            except Exception as e:
                st.error(f"Agent başlatılamadı: {e}")
                return

    agent  = st.session_state[agent_key]
    durum  = agent.status_summary()
    analiz = agent.memory.son_analiz

    # ── Yenile butonu ──
    col_r, col_s = st.columns([4, 1])
    with col_s:
        if st.button("🔄 Yenile", use_container_width=True):
            with st.spinner("Yeniden analiz ediliyor..."):
                agent.analyze()
                st.rerun()

    # ── KPI Satırı ──
    c1,c2,c3,c4,c5 = st.columns(5)
    skor_renk = (C_GREEN if durum["skor"]>=70 else
                 C_YELLOW if durum["skor"]>=50 else C_RED)
    with c1: kpi("CFO Skoru", f'{durum["skor"]}/100',
                 color=skor_renk)
    with c2: kpi("Kategori", durum["kategori"], color=skor_renk)
    with c3: kpi("🔴 Kritik", str(durum["kritik_uyari"]),
                 color=C_RED if durum["kritik_uyari"]>0 else C_GREEN,
                 positive=durum["kritik_uyari"]==0)
    with c4: kpi("🟡 Dikkat", str(durum["dikkat_uyari"]),
                 color=C_YELLOW if durum["dikkat_uyari"]>0 else C_GREEN,
                 positive=durum["dikkat_uyari"]==0)
    with c5: kpi("Risk Profili", durum["risk_profili"], color=C_BLUE)

    # ── Alt Sekmeler ──
    s1, s2, s3, s4, s5 = st.tabs([
        "🚨 Uyarılar",
        "💼 Yatırım Önerileri",
        "🏦 Borç Önerileri",
        "📋 Otomatik Rapor",
        "💬 CFO Sohbet",
    ])

    # ════════════ UYARILAR ════════════
    with s1:
        uyarilar = agent.memory.uyarilar

        if not uyarilar:
            st.success("✅ Aktif uyarı yok — şirket sağlıklı görünüyor.")
        else:
            # Kritikler önce
            for u in uyarilar:
                renk = alert_color(u.seviye)
                bg   = alert_bg(u.seviye)
                st.markdown(
                    f'<div style="background:{bg};border-left:4px solid {renk};'
                    f'border-radius:0 12px 12px 0;padding:14px 18px;margin-bottom:10px;">'
                    f'<div style="color:{renk};font-weight:700;font-size:.9rem;'
                    f'margin-bottom:4px;">{u.seviye} — {u.baslik}</div>'
                    f'<div style="color:#a0b8d0;font-size:.85rem;margin-bottom:6px;">'
                    f'{u.mesaj}</div>'
                    f'<div style="color:{renk};font-size:.82rem;">'
                    f'💡 <b>Öneri:</b> {u.oneri}</div>'
                    f'</div>',
                    unsafe_allow_html=True)

        # AI ile uyarı yorumu
        st.markdown("---")
        if st.button("🤖 Uyarıları AI ile Yorumla", key="ai_uyari"):
            with st.spinner("CFO Agent analiz yapıyor..."):
                yorum = agent.chat(
                    f"Şu anki {len(uyarilar)} uyarıyı özetle ve "
                    f"en öncelikli 3 adımı söyle."
                )
                st.session_state["cfo_uyari_yorum"] = yorum

        if "cfo_uyari_yorum" in st.session_state:
            st.markdown(
                f'<div style="background:#0d1520;border:1px solid #0066ff44;'
                f'border-radius:12px;padding:16px 20px;color:#a8c8e8;'
                f'font-size:.9rem;line-height:1.8;">'
                f'<span style="display:inline-block;background:#0066ff22;'
                f'border:1px solid #0066ff44;color:#60a5fa;font-size:.7rem;'
                f'padding:2px 8px;border-radius:20px;margin-bottom:8px;">CFO Agent</span><br>'
                f'{st.session_state["cfo_uyari_yorum"].replace(chr(10),"<br>")}'
                f'</div>',
                unsafe_allow_html=True)

    # ════════════ YATIRIM ÖNERİLERİ ════════════
    with s2:
        inv = analiz["inv"]
        sec(f"💼 Yatırım Profili: {inv['risk_profili']}")

        c1,c2 = st.columns(2)
        with c1: kpi("Yıllık Gelir",   fmt(inv["yillik_gelir"]))
        with c2: kpi("Maks. Yatırım",   fmt(inv["max_yatirim"]),
                     "Mevcut nakitin %40'ı")

        st.markdown("---")
        for i, oneri in enumerate(inv["oneriler"], 1):
            oncelik_renk = C_RED if oneri["oncelik"]=="Yüksek" else C_YELLOW
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1e3a5f;'
                f'border-radius:12px;padding:16px 18px;margin-bottom:10px;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;margin-bottom:8px;">'
                f'<span style="font-family:Syne,sans-serif;font-weight:700;'
                f'color:#e8eaf0;font-size:.95rem;">{i}. {oneri["tip"]}</span>'
                f'<span style="background:{oncelik_renk}22;color:{oncelik_renk};'
                f'font-size:.72rem;padding:2px 8px;border-radius:20px;">'
                f'{oneri["oncelik"]} Öncelik</span></div>'
                f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">'
                f'<div style="color:#4a6fa5;font-size:.78rem;">Tutar<br>'
                f'<span style="color:#60a5fa;font-weight:600;">{fmt(oneri["tutar"])}</span></div>'
                f'<div style="color:#4a6fa5;font-size:.78rem;">Süre<br>'
                f'<span style="color:#e8eaf0;">{oneri["sure"]}</span></div>'
                f'<div style="color:#4a6fa5;font-size:.78rem;">Beklenen ROI<br>'
                f'<span style="color:#10d994;font-weight:600;">{oneri["beklenen_roi"]}</span></div>'
                f'</div></div>',
                unsafe_allow_html=True)

        if st.button("🤖 Yatırım Stratejisi Sor", key="ai_inv"):
            with st.spinner("CFO Agent düşünüyor..."):
                cevap = agent.chat(
                    f"Risk profilim {inv['risk_profili']}. "
                    f"Yıllık gelirimin {fmt(inv['yillik_gelir'])} olduğunu düşünerek "
                    f"öncelikli yatırım stratejimi açıkla."
                )
                st.session_state["cfo_inv_yorum"] = cevap

        if "cfo_inv_yorum" in st.session_state:
            st.markdown(
                f'<div style="background:#0d1520;border:1px solid #0066ff44;'
                f'border-radius:12px;padding:16px 20px;color:#a8c8e8;'
                f'font-size:.9rem;line-height:1.8;margin-top:10px;">'
                f'{st.session_state["cfo_inv_yorum"].replace(chr(10),"<br>")}'
                f'</div>', unsafe_allow_html=True)

    # ════════════ BORÇ ÖNERİLERİ ════════════
    with s3:
        debt = analiz["debt"]
        sec("🏦 Borç Yönetimi Analizi")

        c1,c2,c3 = st.columns(3)
        with c1: kpi("Toplam Borç", fmt(debt["mevcut_borc"]),
                     positive=False, color=C_RED)
        with c2: kpi("Ort. Faiz", f'%{debt["faiz_orani_pct"]}',
                     positive=debt["faiz_orani_pct"]<35,
                     color=C_GREEN if debt["faiz_orani_pct"]<35 else C_RED)
        with c3: kpi("B/G Oranı", str(debt["borc_gelir_orani"]),
                     "Hedef: < 2",
                     positive=debt["borc_gelir_orani"]<2,
                     color=C_GREEN if debt["borc_gelir_orani"]<2 else C_RED)

        st.markdown("---")
        if debt["oneriler"]:
            for oneri in debt["oneriler"]:
                st.markdown(
                    f'<div style="background:#111827;border:1px solid #1e3a5f;'
                    f'border-radius:12px;padding:14px 18px;margin-bottom:8px;">'
                    f'<div style="font-weight:700;color:#e8eaf0;margin-bottom:6px;">'
                    f'🏦 {oneri["tip"]}</div>'
                    f'<div style="color:#8aabcc;font-size:.85rem;margin-bottom:4px;">'
                    f'{oneri["aciklama"]}</div>'
                    f'<div style="color:{C_CYAN};font-size:.84rem;">'
                    f'➡️ {oneri["eylem"]}</div>'
                    + (f'<div style="color:{C_GREEN};font-size:.82rem;margin-top:4px;">'
                       f'💰 Potansiyel tasarruf: {fmt(oneri["tasarruf"])}</div>'
                       if oneri.get("tasarruf", 0) > 0 else "") +
                    f'</div>', unsafe_allow_html=True)
        else:
            st.info("Borç girişi yapılmamış. 'Borç Analizi' sekmesinden borç verilerini girin.")

        if st.button("🤖 Borç Stratejisi Sor", key="ai_debt"):
            with st.spinner("CFO Agent düşünüyor..."):
                cevap = agent.chat(
                    "Mevcut borç yapım ve faiz oranlarım göz önünde bulundurularak "
                    "en optimal borç yönetimi stratejisini öner."
                )
                st.session_state["cfo_debt_yorum"] = cevap

        if "cfo_debt_yorum" in st.session_state:
            st.markdown(
                f'<div style="background:#0d1520;border:1px solid #0066ff44;'
                f'border-radius:12px;padding:16px 20px;color:#a8c8e8;'
                f'font-size:.9rem;line-height:1.8;margin-top:10px;">'
                f'{st.session_state["cfo_debt_yorum"].replace(chr(10),"<br>")}'
                f'</div>', unsafe_allow_html=True)

    # ════════════ OTOMATİK RAPOR ════════════
    with s4:
        sec("📋 Otomatik Periyodik Rapor")

        col1, col2 = st.columns(2)
        with col1:
            periyot = st.selectbox(
                "Rapor Periyodu",
                ["Günlük", "Haftalık", "Aylık", "Çeyreklik"],
                index=2, key="cfo_periyot"
            )
        with col2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("📄 Rapor Üret", use_container_width=True, key="cfo_rapor_btn"):
                with st.spinner("Rapor hazırlanıyor..."):
                    rapor_md = agent.generate_report(periyot=periyot)
                    st.session_state["cfo_rapor_md"] = rapor_md

        if "cfo_rapor_md" in st.session_state:
            rapor_md = st.session_state["cfo_rapor_md"]
            st.markdown(
                f'<div style="background:#0d1520;border:1px solid #1e3a5f;'
                f'border-radius:14px;padding:20px 24px;color:#a8c8e8;'
                f'font-size:.88rem;line-height:1.8;white-space:pre-wrap;">'
                f'{rapor_md}</div>', unsafe_allow_html=True)

            # İndir
            st.download_button(
                "⬇ Raporu İndir (.md)",
                rapor_md.encode("utf-8"),
                f"cfo_rapor_{datetime.now().strftime('%Y%m%d')}.md",
                "text/markdown",
                use_container_width=True,
            )

            # AI ile zenginleştir
            if st.button("🤖 Raporu AI ile Zenginleştir", key="cfo_enrich"):
                with st.spinner("CFO Agent raporu zenginleştiriyor..."):
                    zengin = agent.chat(
                        "Az önce üretilen raporu oku ve eksik olan kritik "
                        "finansal bilgileri, rakam bazlı analizleri ve "
                        "somut aksiyon maddelerini ekleyerek zenginleştir."
                    )
                    st.session_state["cfo_rapor_zengin"] = zengin

            if "cfo_rapor_zengin" in st.session_state:
                st.markdown("---")
                sec("🤖 AI Tarafından Zenginleştirilmiş Rapor")
                st.markdown(
                    f'<div style="background:#0d1520;border:1px solid #0066ff44;'
                    f'border-radius:14px;padding:20px 24px;color:#a8c8e8;'
                    f'font-size:.88rem;line-height:1.8;">'
                    f'{st.session_state["cfo_rapor_zengin"].replace(chr(10),"<br>")}'
                    f'</div>', unsafe_allow_html=True)

    # ════════════ CFO SOHBET ════════════
    with s5:
        sec("💬 CFO ile Sohbet")
        st.markdown(
            '<div style="color:#4a6fa5;font-size:.82rem;margin-bottom:16px;">'
            'Şirket verilerinizi bilen CFO AI Agent ile finansal kararlarınız '
            'hakkında konuşun.</div>', unsafe_allow_html=True)

        # Hızlı sorular
        hizli_sorular = [
            "En acil finansal sorunum nedir?",
            "Bu ay ne yapmalıyım?",
            "Kredi almalı mıyım?",
            "Büyüme için hazır mıyım?",
        ]
        cols = st.columns(4)
        for col, soru in zip(cols, hizli_sorular):
            with col:
                if st.button(soru, key=f"cfo_hs_{soru}", use_container_width=True):
                    with st.spinner("CFO düşünüyor..."):
                        cevap = agent.chat(soru)
                    st.session_state["cfo_chat"] = st.session_state.get("cfo_chat", [])
                    st.session_state["cfo_chat"].append({"role":"user","content":soru})
                    st.session_state["cfo_chat"].append({"role":"cfo","content":cevap})
                    st.rerun()

        st.markdown("---")

        # Sohbet geçmişi
        chat_history = st.session_state.get("cfo_chat", [])
        for msg in chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="background:#1a2d50;border-radius:12px 12px 4px 12px;'
                    f'padding:10px 14px;margin:6px 0 6px 60px;'
                    f'font-size:.9rem;color:#c8d8f0;">👤 {msg["content"]}</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:#111827;border:1px solid #1e3a5f;'
                    f'border-radius:12px 12px 12px 4px;'
                    f'padding:10px 14px;margin:6px 60px 6px 0;'
                    f'font-size:.9rem;color:#a8c0e0;">🧠 {msg["content"]}</div>',
                    unsafe_allow_html=True)

        # Giriş
        ci, cs = st.columns([5, 1])
        with ci:
            user_in = st.text_input(
                "CFO'ya sorun...", key="cfo_input",
                label_visibility="collapsed",
                placeholder="Örn: Nakit sıkışıklığı yaşarsam ne yapmalıyım?")
        with cs:
            if st.button("➤", use_container_width=True, key="cfo_send") and user_in:
                with st.spinner("CFO düşünüyor..."):
                    cevap = agent.chat(user_in)
                chat_history.append({"role":"user","content":user_in})
                chat_history.append({"role":"cfo","content":cevap})
                st.session_state["cfo_chat"] = chat_history
                st.rerun()

        if chat_history:
            if st.button("🗑 Sohbeti Temizle", key="cfo_clear"):
                agent.reset_chat()
                st.session_state["cfo_chat"] = []
                st.rerun()
