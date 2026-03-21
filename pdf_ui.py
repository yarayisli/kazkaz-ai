"""
KazKaz AI - PDF Rapor Streamlit Entegrasyonu
=============================================
Bu modülü app.py içine import edin ve sidebar'a ekleyin.

Kullanım (app.py içinde):
    from pdf_ui import show_pdf_download_button
    # Sidebar veya herhangi bir sekme içinde:
    show_pdf_download_button(rapor, engine, sirket_adi, ai_yorum, senaryo, tahmin)
"""

import streamlit as st
from pdf_report import PDFReportGenerator


def show_pdf_download_button(
    rapor:       dict,
    engine,
    sirket_adi:  str  = "Şirketim",
    ai_yorum:    str  = None,
    senaryo:     dict = None,
    tahmin:      dict = None,
    key:         str  = "pdf_btn",
):
    """
    Tek tıkla PDF rapor indirme butonu.
    app.py içindeki herhangi bir yere eklenebilir.
    """
    if st.button("📄 PDF Rapor İndir", use_container_width=True, key=key):
        with st.spinner("PDF hazırlanıyor..."):
            try:
                gen = PDFReportGenerator(
                    rapor=rapor,
                    engine=engine,
                    sirket_adi=sirket_adi,
                    ai_yorum=ai_yorum,
                    senaryo=senaryo,
                    tahmin=tahmin,
                )
                pdf_bytes = gen.generate()
                st.session_state["pdf_bytes"] = pdf_bytes
                st.success("✅ PDF hazır!")
            except Exception as e:
                st.error(f"PDF hatası: {e}")

    if "pdf_bytes" in st.session_state:
        from datetime import datetime
        dosya_adi = f"kazkaz_rapor_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        st.download_button(
            label="⬇ PDF İndir",
            data=st.session_state["pdf_bytes"],
            file_name=dosya_adi,
            mime="application/pdf",
            use_container_width=True,
            key=f"{key}_download",
        )


# ─────────────────────────────────────────────
# app.py'e NASIL EKLENİR
# ─────────────────────────────────────────────
# 1. Import ekle:
#    from pdf_ui import show_pdf_download_button
#
# 2. Sidebar'a ekle (veri yükleme bölümünün altına):
#    if st.session_state.rapor and plan_gate("pdf_rapor"):
#        st.markdown("---")
#        show_pdf_download_button(
#            rapor       = st.session_state.rapor,
#            engine      = st.session_state.engine,
#            sirket_adi  = st.session_state.get("sirket_adi", "Şirketim"),
#            ai_yorum    = st.session_state.get("ai_analiz"),
#            senaryo     = st.session_state.get("senaryo_sonuc"),
#            tahmin      = st.session_state.get("forecast"),
#        )
