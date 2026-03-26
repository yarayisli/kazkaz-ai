"""
KazKaz AI - Veri Giriş Merkezi Streamlit Modülü
================================================
Üç yöntem:
  1. Akıllı dosya yükleme (Logo/Mikro/Zirve/Excel otomatik)
  2. Manuel aylık giriş formu
  3. Google Sheets bağlantısı (opsiyonel)

app.py entegrasyonu:
    from data_entry_ui import show_data_entry
    # Sidebar içinde:
    df = show_data_entry()
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from io import BytesIO

from design_system import *

try:
    from data_importer import DataImporter
    IMPORTER_OK = True
except ImportError:
    IMPORTER_OK = False



def show_data_entry_tab():
    """Tam sayfa veri giriş merkezi."""

    st.markdown(
        '<div style="font-family:Inter,-apple-system,sans-serif;font-size:1.5rem;font-weight:800;'
        'background:linear-gradient(135deg,#0EA5E9,#1D4ED8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '📥 Veri Giriş Merkezi</div>'
        '<div style="color:#64748B;font-size:.78rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:18px;">'
        'Excel Upload · Logo/Mikro/Zirve · Manuel Giriş</div>',
        unsafe_allow_html=True)

    s1, s2, s3, s4 = st.tabs([
        "📁 Dosya Yükle",
        "✏️ Manuel Giriş",
        "📋 Şablon İndir",
        "📊 Mevcut Veri",
    ])

    # ════════ DOSYA YÜKLE ════════
    with s1:
        sec("📁 Akıllı Dosya Yükleme")
        st.markdown(
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            'border-radius:12px;padding:14px 18px;margin-bottom:16px;">'
            '<div style="color:#1D4ED8;font-weight:700;font-size:.88rem;'
            'margin-bottom:8px;">✅ Desteklenen Formatlar</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;'
            'gap:6px;font-size:.82rem;color:#4B5563;">'
            '<div>📊 KazKaz Standart (CSV/Excel)</div>'
            '<div>🔷 Logo Yazılım Export</div>'
            '<div>🔶 Mikro Muhasebe Export</div>'
            '<div>🔵 Zirve Export</div>'
            '<div>📄 Netsis Export</div>'
            '<div>📋 Muhasebeci Excel (Genel)</div>'
            '</div></div>',
            unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Dosyanızı sürükleyin veya tıklayın",
            type=["csv", "xlsx", "xls"],
            key="data_upload_main",
            label_visibility="collapsed",
        )

        if uploaded and IMPORTER_OK:
            with st.spinner("Dosya analiz ediliyor..."):
                try:
                    importer = DataImporter()
                    df, bilgi = importer.import_file(
                        uploaded, uploaded.name)
                    st.session_state["uploaded_df"]   = df
                    st.session_state["upload_bilgi"]  = bilgi
                    st.success(
                        f"✅ **{bilgi['format']}** formatı algılandı — "
                        f"{bilgi['temiz_satirlar']} kayıt yüklendi.")
                except Exception as e:
                    st.error(f"❌ {e}")

            # Bilgi kartı
            if "upload_bilgi" in st.session_state:
                b = st.session_state["upload_bilgi"]
                c1,c2,c3,c4 = st.columns(4)
                with c1:
                    st.metric("Format",     b["format"])
                with c2:
                    st.metric("Kayıt Sayısı", b["temiz_satirlar"])
                with c3:
                    v = b["toplam_gelir"]
                    st.metric("Toplam Gelir",
                              f'{v/1000:.0f}K ₺' if v>=1000 else f'{v:,.0f} ₺')
                with c4:
                    v = b["toplam_gider"]
                    st.metric("Toplam Gider",
                              f'{v/1000:.0f}K ₺' if v>=1000 else f'{v:,.0f} ₺')

                # Önizleme
                sec("👁️ Veri Önizleme")
                st.dataframe(
                    st.session_state["uploaded_df"].head(10),
                    use_container_width=True, hide_index=True)

                # Uygula butonu
                if st.button("✅ Bu Veriyi Analizde Kullan",
                             use_container_width=True,
                             type="primary", key="apply_upload"):
                    st.session_state["df_final"] = st.session_state["uploaded_df"]
                    st.success("✅ Veri analize yüklendi! Sol panelden 'Analizi Başlat' butonuna tıklayın.")

        elif uploaded and not IMPORTER_OK:
            st.warning("data_importer.py bulunamadı — standart yükleme kullanılıyor.")

    # ════════ MANUEL GİRİŞ ════════
    with s2:
        sec("✏️ Aylık Manuel Veri Girişi")
        st.markdown(
            '<div style="color:#64748B;font-size:.82rem;margin-bottom:12px;">'
            'Muhasebe programınız yoksa veya hızlıca veri girmek istiyorsanız '
            'kullanın. Her satır bir dönem/kategori kombinasyonu.</div>',
            unsafe_allow_html=True)

        # Mevcut kayıtları göster
        if "manuel_satirlar" not in st.session_state:
            st.session_state["manuel_satirlar"] = [
                {"tarih":"2024-01","kategori":"Satış","gelir":0,"gider":0},
            ]

        satirlar = st.session_state["manuel_satirlar"]

        # Kolon başlıkları
        ch = st.columns([2,3,2,2,1])
        basliklar = ["Dönem (YYYY-MM)","Kategori","Gelir (₺)","Gider (₺)",""]
        for col, b in zip(ch, basliklar):
            col.markdown(
                f'<div style="color:#64748B;font-size:.75rem;'
                f'text-transform:uppercase;letter-spacing:1px;'
                f'padding-bottom:4px;">{b}</div>',
                unsafe_allow_html=True)

        # Satırları göster
        to_delete = []
        for i, satir in enumerate(satirlar):
            c1,c2,c3,c4,c5 = st.columns([2,3,2,2,1])
            with c1:
                yil  = st.selectbox("",
                    [str(y) for y in range(2020, datetime.now().year+2)],
                    index=[str(y) for y in range(2020, datetime.now().year+2)].index(
                        satir["tarih"][:4]),
                    key=f"m_yil_{i}", label_visibility="collapsed")
                ay   = st.selectbox("",
                    [f"{m:02d}" for m in range(1,13)],
                    index=int(satir["tarih"][5:7])-1,
                    key=f"m_ay_{i}", label_visibility="collapsed")
                satirlar[i]["tarih"] = f"{yil}-{ay}"
            with c2:
                kat_options = [
                    "Satış", "Hizmet Geliri", "Kira Geliri",
                    "Personel Gideri", "Kira Gideri", "Pazarlama",
                    "Hammadde", "Genel Gider", "Vergi", "Diğer",
                ]
                if satir["kategori"] not in kat_options:
                    kat_options.insert(0, satir["kategori"])
                satirlar[i]["kategori"] = st.selectbox(
                    "", kat_options,
                    index=kat_options.index(satir["kategori"]),
                    key=f"m_kat_{i}", label_visibility="collapsed")
            with c3:
                satirlar[i]["gelir"] = st.number_input(
                    "", min_value=0, value=int(satir["gelir"]),
                    step=1000, key=f"m_gelir_{i}",
                    label_visibility="collapsed")
            with c4:
                satirlar[i]["gider"] = st.number_input(
                    "", min_value=0, value=int(satir["gider"]),
                    step=1000, key=f"m_gider_{i}",
                    label_visibility="collapsed")
            with c5:
                if st.button("🗑", key=f"m_del_{i}"):
                    to_delete.append(i)

        # Silme işlemi
        for idx in sorted(to_delete, reverse=True):
            st.session_state["manuel_satirlar"].pop(idx)
            st.rerun()

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Satır Ekle", use_container_width=True):
                son = satirlar[-1]["tarih"] if satirlar else "2024-01"
                yil, ay = int(son[:4]), int(son[5:7])
                ay += 1
                if ay > 12:
                    ay = 1
                    yil += 1
                st.session_state["manuel_satirlar"].append(
                    {"tarih": f"{yil}-{ay:02d}",
                     "kategori": "Satış", "gelir": 0, "gider": 0})
                st.rerun()

        with col2:
            if st.button("📋 12 Ay Şablon Yükle", use_container_width=True):
                yil = datetime.now().year
                yeni = []
                for ay in range(1, 13):
                    for kat, tip in [("Satış","gelir"),("Personel Gideri","gider"),
                                     ("Kira Gideri","gider")]:
                        entry = {"tarih": f"{yil}-{ay:02d}",
                                 "kategori": kat, "gelir": 0, "gider": 0}
                        yeni.append(entry)
                st.session_state["manuel_satirlar"] = yeni
                st.rerun()

        with col3:
            if st.button("✅ Girişi Kaydet & Analiz Et",
                         use_container_width=True, type="primary"):
                if IMPORTER_OK:
                    df = DataImporter.from_manual_entries(
                        st.session_state["manuel_satirlar"])
                else:
                    # Fallback
                    rows = []
                    for e in st.session_state["manuel_satirlar"]:
                        if float(e.get("gelir",0)) + float(e.get("gider",0)) > 0:
                            rows.append({
                                "Tarih":    e["tarih"],
                                "Kategori": e["kategori"],
                                "Gelir":    float(e.get("gelir",0)),
                                "Gider":    float(e.get("gider",0)),
                            })
                    df = pd.DataFrame(rows)

                if not df.empty:
                    st.session_state["df_final"] = df
                    st.success(f"✅ {len(df)} kayıt kaydedildi!")
                else:
                    st.warning("Hiç veri girilmedi.")

    # ════════ ŞABLON İNDİR ════════
    with s3:
        sec("📋 Excel Şablonları")

        st.markdown(
            '<div style="color:#64748B;font-size:.83rem;margin-bottom:16px;">'
            'Muhasebecilere gönderebileceğiniz veya kendiniz doldurabileceğiniz '
            'hazır şablonlar.</div>',
            unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E2E8F0;'
                'border-radius:12px;padding:16px;margin-bottom:12px;">'
                '<div style="color:#1D4ED8;font-weight:700;margin-bottom:8px;">'
                '📊 Temel Şablon</div>'
                '<div style="color:#64748B;font-size:.82rem;">'
                'Tarih, Kategori, Gelir, Gider sütunları.<br>'
                'En basit format — herkese uyar.</div></div>',
                unsafe_allow_html=True)

            if IMPORTER_OK:
                temel = DataImporter.standart_sablon()
            else:
                temel = pd.DataFrame({
                    "Tarih":    ["2024-01","2024-01","2024-02"],
                    "Kategori": ["Satış","Personel","Satış"],
                    "Gelir":    [150000,0,170000],
                    "Gider":    [0,45000,0],
                })

            buf = BytesIO()
            temel.to_excel(buf, index=False)
            st.download_button(
                "⬇ Temel Şablonu İndir (.xlsx)",
                buf.getvalue(),
                "kazkaz_sablon_temel.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col2:
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E2E8F0;'
                'border-radius:12px;padding:16px;margin-bottom:12px;">'
                '<div style="color:#059669;font-weight:700;margin-bottom:8px;">'
                '🎯 Gelişmiş Şablon</div>'
                '<div style="color:#64748B;font-size:.82rem;">'
                'Müşteri, Ürün sütunları dahil.<br>'
                'Müşteri & ürün analizi için gerekli.</div></div>',
                unsafe_allow_html=True)

            gelismis = pd.DataFrame({
                "Tarih":    ["2024-01","2024-01","2024-02","2024-02"],
                "Kategori": ["Satış","Kira Gideri","Satış","Personel"],
                "Gelir":    [150000,0,200000,0],
                "Gider":    [0,12000,0,55000],
                "Müşteri":  ["Acme A.Ş.","","Beta Ltd.",""],
                "Ürün":     ["ERP","","CRM",""],
            })

            buf2 = BytesIO()
            gelismis.to_excel(buf2, index=False)
            st.download_button(
                "⬇ Gelişmiş Şablonu İndir (.xlsx)",
                buf2.getvalue(),
                "kazkaz_sablon_gelismis.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        # Muhasebeciye gönderilecek açıklama
        st.markdown("---")
        sec("📧 Muhasebecinize Gönderebileceğiniz Açıklama")
        st.markdown(
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            'border-radius:12px;padding:16px 20px;font-size:.85rem;'
            'color:#a0b8d0;line-height:1.8;">'
            'Merhaba,<br><br>'
            'Aylık finansal verilerimi KazKaz AI platformuna yükleyebilmem için '
            'aşağıdaki Excel formatında gönderebilir misiniz?<br><br>'
            '<b style="color:#1D4ED8;">Gerekli sütunlar:</b><br>'
            '• <b>Tarih</b>: YYYY-MM formatında (örn: 2024-01)<br>'
            '• <b>Kategori</b>: Hesap adı veya işlem türü<br>'
            '• <b>Gelir</b>: Gelir tutarı (₺ cinsinden, gider satırlarında 0)<br>'
            '• <b>Gider</b>: Gider tutarı (₺ cinsinden, gelir satırlarında 0)<br><br>'
            'Şablonu ekte bulabilirsiniz. Logo/Mikro/Zirve export da kabul edilir.<br><br>'
            'Teşekkürler.</div>',
            unsafe_allow_html=True)

        # Kopyala butonu
        mesaj = """Merhaba,

Aylık finansal verilerimi KazKaz AI platformuna yüklemek için aşağıdaki formatta Excel gönderebilir misiniz?

Sütunlar:
- Tarih (YYYY-MM formatı, örn: 2024-01)
- Kategori (hesap adı)
- Gelir (TL, gider satırlarında 0)
- Gider (TL, gelir satırlarında 0)

Logo/Mikro/Zirve export da kabul edilir.

Teşekkürler."""
        st.download_button(
            "📋 Açıklamayı TXT Olarak İndir",
            mesaj.encode("utf-8"),
            "muhasebeci_bilgi.txt", "text/plain",
            use_container_width=True,
        )

    # ════════ MEVCUT VERİ ════════
    with s4:
        sec("📊 Yüklü Veri Durumu")

        df_key = "df_final"
        if df_key not in st.session_state:
            df_key = "uploaded_df"

        if df_key in st.session_state:
            df = st.session_state[df_key]
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Toplam Kayıt",  len(df))
            with c2: st.metric("Dönem Sayısı",
                                df["Tarih"].nunique() if "Tarih" in df.columns else "-")
            with c3: st.metric("Toplam Gelir",
                                f'{df["Gelir"].sum()/1000:.0f}K ₺'
                                if "Gelir" in df.columns else "-")
            with c4: st.metric("Toplam Gider",
                                f'{df["Gider"].sum()/1000:.0f}K ₺'
                                if "Gider" in df.columns else "-")

            st.dataframe(df, use_container_width=True, hide_index=True)

            # İndir
            buf = BytesIO()
            df.to_excel(buf, index=False)
            st.download_button(
                "⬇ Mevcut Veriyi İndir (.xlsx)",
                buf.getvalue(),
                "kazkaz_veri.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

            # Temizle
            if st.button("🗑 Veriyi Sil ve Sıfırla", key="clear_data"):
                for k in ["df_final","uploaded_df","upload_bilgi","manuel_satirlar"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        else:
            st.info("Henüz veri yüklenmemiş. 'Dosya Yükle' veya 'Manuel Giriş' sekmesini kullanın.")
