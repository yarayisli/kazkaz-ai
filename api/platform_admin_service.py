"""KazKaz platform yöneticisi için veri minimizasyonlu işletim görünümü.

Bu servis çalışma alanı belgelerini veya finansal girdileri okumaz. Yalnız şirket
üst bilgisi, üye adedi, geri bildirim durumu ve denetim olayı gibi işletim
metadatasını döndürür.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
from typing import Any

from fastapi import HTTPException
from firebase_admin import firestore
from firebase_admin import auth as firebase_auth

from api.auth import _firebase_uygulamasi
from api.models import (
    KimlikBilgisi,
    PlatformGeriBildirimDurumIstegi,
    PlatformSirketEylemIstegi,
    PlatformSirketGuncellemeIstegi,
)
from api.company_service import _claimleri_guncelle


def _iso(deger: Any) -> str | None:
    if isinstance(deger, (datetime, date)):
        return deger.isoformat()
    if isinstance(deger, str):
        return deger[:40]
    return None


def _durum(veri: dict) -> str:
    durum = str(veri.get("status") or "active").lower()
    if durum in {"active", "pilot", "suspended", "closed"}:
        return durum
    return "active"


def _eposta_maskele(eposta: Any) -> str:
    """Platform operasyonuna kişi adresini açmadan tanınabilir bir ipucu verir."""
    deger = str(eposta or "").strip().lower()
    if "@" not in deger:
        return "gizli"
    yerel, alan = deger.split("@", 1)
    alan_parcalari = alan.split(".")
    alan_adi = alan_parcalari[0]
    uzanti = ".".join(alan_parcalari[1:])
    maskeli_alan = (alan_adi[:1] + "***") if alan_adi else "***"
    if uzanti:
        maskeli_alan += f".{uzanti}"
    return f"{yerel[:1] or '*'}***@{maskeli_alan}"


def _aktor_ozeti(kimlik: Any) -> str:
    if not kimlik:
        return "sistem"
    return "usr_" + hashlib.sha256(str(kimlik).encode("utf-8")).hexdigest()[:10]


def _datetime(deger: Any) -> datetime | None:
    if isinstance(deger, datetime):
        return deger if deger.tzinfo else deger.replace(tzinfo=timezone.utc)
    if isinstance(deger, str):
        try:
            sonuc = datetime.fromisoformat(deger.replace("Z", "+00:00"))
            return sonuc if sonuc.tzinfo else sonuc.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _aktivite_ozeti(audit_kayitlari: list[dict]) -> dict:
    sirali = sorted(
        audit_kayitlari,
        key=lambda kayit: _datetime(kayit.get("createdAt")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    esik = datetime.now(timezone.utc) - timedelta(days=30)
    son_otuz = [kayit for kayit in sirali if (_datetime(kayit.get("createdAt")) or datetime.min.replace(tzinfo=timezone.utc)) >= esik]
    aksiyonlar = Counter(str(kayit.get("action") or "unknown") for kayit in audit_kayitlari)
    son = sirali[0] if sirali else {}
    son_workspace = next((kayit for kayit in sirali if str(kayit.get("action", "")).startswith("workspace.")), None)
    return {
        "son_aktivite": _iso(son.get("createdAt")),
        "son_aksiyon": str(son.get("action") or "aktivite_yok")[:80],
        "aktivite_30_gun": len(son_otuz),
        "rapor_arsivleme": aksiyonlar["report.archive"],
        "rapor_indirme": aksiyonlar["report.download"],
        "calisma_alani_kayit": aksiyonlar["workspace.save"],
        "calisma_alani_okuma": aksiyonlar["workspace.read"],
        "calisma_alani_disari_aktarma": aksiyonlar["workspace.export"],
        "uyelik_islemi": sum(adet for ad, adet in aksiyonlar.items() if ad.startswith("member.")),
        "veri_durumu": (
            "silindi" if son_workspace and son_workspace.get("action") == "workspace.delete"
            else "kayitli" if son_workspace else "veri_yok"
        ),
        "aksiyon_dagilimi": dict(aksiyonlar.most_common(12)),
    }


def _db():
    return firestore.client(app=_firebase_uygulamasi())


def _son_kayitlar(collection_ref, n: int):
    """createdAt'e göre en yeni n kaydı getirir.

    order_by olmadan limit, gelişigüzel bir alt küme döndürür; "son aktivite"
    o küme içinden hesaplandığı için gerçek en yeni kayıt dışarıda kalabilirdi.
    Sıralama seçimi doğrular; çağıran taraf yine kendi içinde sıralar.
    """
    return collection_ref.order_by(
        "createdAt", direction=firestore.Query.DESCENDING
    ).limit(n)


def _toplam_sirket_sayisi() -> "int | None":
    """Şirketlerin gerçek toplam sayısı (aggregation). Okunamazsa None döner."""
    try:
        db = _db()
        try:
            aggregate = db.collection("companies").count()
            return int(aggregate.get()[0][0].value)
        except Exception:
            return sum(1 for _ in db.collection("companies").stream())
    except Exception:
        return None


def _count(query) -> int:
    """
    Firestore aggregation count — server-side sayım.
    Fallback: aggregation desteklenmiyorsa stream (test/mock).
    Etki: subcollection başına N doc read → 1 aggregation read; ayrıca
    ağ üzerinden döküman payload'u aktarılmaz. Prod'da 100 şirket
    admin dashboard'unda ~400 stream call'dan tek digit aggregation
    call'a düşülür.
    """
    try:
        aggregate = query.count()
        results = aggregate.get()
        return int(results[0][0].value)
    except Exception:
        try:
            return sum(1 for _ in query.stream())
        except Exception:
            return 0


def platform_sirketleri(limit: int = 50) -> dict:
    """Finansal değer, dosya veya çalışma alanı içeriği olmadan şirketleri listeler."""
    try:
        db = _db()
        satirlar = []
        for belge in db.collection("companies").limit(limit).stream():
            veri = belge.to_dict() or {}
            # Denormalize alan varsa onu kullan (0 network); yoksa aggregation
            # count. En son çare stream.
            stats = veri.get("stats") if isinstance(veri.get("stats"), dict) else {}
            uye_sayisi = int(stats.get("memberCount", -1))
            if uye_sayisi < 0:
                uye_sayisi = _count(belge.reference.collection("members").limit(500))

            bekleyen_davet = int(stats.get("pendingInviteCount", -1))
            if bekleyen_davet < 0:
                bekleyen_davet = _count(
                    belge.reference.collection("invitations")
                        .where("status", "==", "pending")
                        .limit(200)
                )

            yeni_geri_bildirim = int(stats.get("newFeedbackCount", -1))
            if yeni_geri_bildirim < 0:
                yeni_geri_bildirim = _count(
                    belge.reference.collection("feedback")
                        .where("status", "==", "new")
                        .limit(200)
                )

            # Audit özeti gerçekten dokuman payload'una ihtiyaç duyuyor,
            # aggregation ile veremeyiz — ama limit 300 → 50 yapabiliriz;
            # aktivite özeti son N kayıt için yeter.
            audit_kayitlari = [
                audit.to_dict() or {}
                for audit in _son_kayitlar(belge.reference.collection("auditLogs"), 50).stream()
            ]
            aktivite = _aktivite_ozeti(audit_kayitlari)
            profil = veri.get("profile") if isinstance(veri.get("profile"), dict) else {}
            sirket_durumu = _durum(veri)
            operasyon_sagligi = (
                "engelli" if sirket_durumu in {"suspended", "closed"}
                else "dikkat" if yeni_geri_bildirim > 0
                else "hareketsiz" if aktivite["son_aktivite"] is None
                else "normal"
            )
            satirlar.append({
                "sirket_id": belge.id,
                "sirket_adi": str(veri.get("name") or veri.get("companyName") or "Adsız şirket")[:160],
                "plan": str(veri.get("plan") or "free").lower(),
                "durum": sirket_durumu,
                "uye_sayisi": uye_sayisi,
                "bekleyen_davet": bekleyen_davet,
                "yeni_geri_bildirim": yeni_geri_bildirim,
                "olusturulma": _iso(veri.get("createdAt")),
                "deneme_bitis": _iso(veri.get("trialEndsAt")),
                "sektor": str(profil.get("sector") or "belirtilmedi")[:40],
                "calisan_olcegi": str(profil.get("employeeScale") or "belirtilmedi")[:20],
                "veri_kaynagi": str(profil.get("dataSource") or "belirtilmedi")[:40],
                "son_aktivite": aktivite["son_aktivite"],
                "son_aksiyon": aktivite["son_aksiyon"],
                "aktivite_30_gun": aktivite["aktivite_30_gun"],
                "rapor_arsivleme": aktivite["rapor_arsivleme"],
                "veri_durumu": aktivite["veri_durumu"],
                "operasyon_sagligi": operasyon_sagligi,
            })
        satirlar.sort(key=lambda item: (item["durum"] != "active", item["sirket_adi"].lower()))
        return {"durum": "hazir", "sirketler": satirlar, "sinir": limit, "finansal_veri_gosterilir": False}
    except Exception:
        return {"durum": "veri_kaynagi_kullanilamiyor", "sirketler": [], "sinir": limit, "finansal_veri_gosterilir": False}


#: platform_olaylari kaç şirketi tarar (olay derlemesi bu örneklemle sınırlı).
OLAY_TARAMA_SINIRI = 50


def platform_olaylari(limit: int = 50) -> dict:
    """Mesaj gövdesi ve finansal değer içermeyen destek/denetim olayları."""
    try:
        db = _db()
        olaylar: list[dict] = []
        for sirket in db.collection("companies").limit(OLAY_TARAMA_SINIRI).stream():
            sirket_verisi = sirket.to_dict() or {}
            sirket_adi = str(sirket_verisi.get("name") or sirket_verisi.get("companyName") or "Adsız şirket")[:160]
            for belge in _son_kayitlar(sirket.reference.collection("feedback"), 30).stream():
                veri = belge.to_dict() or {}
                olaylar.append({
                    "olay_id": belge.id,
                    "tur": "geri_bildirim",
                    "sirket_id": sirket.id,
                    "sirket_adi": sirket_adi,
                    "etiket": str(veri.get("category") or "geri_bildirim")[:40],
                    "sayfa": str(veri.get("page") or "bilinmiyor")[:80],
                    "durum": str(veri.get("status") or "new")[:20],
                    "zaman": _iso(veri.get("createdAt")),
                })
            for belge in _son_kayitlar(sirket.reference.collection("auditLogs"), 30).stream():
                veri = belge.to_dict() or {}
                olaylar.append({
                    "olay_id": belge.id,
                    "tur": "denetim",
                    "sirket_id": sirket.id,
                    "sirket_adi": sirket_adi,
                    "etiket": str(veri.get("action") or "audit")[:80],
                    "sayfa": None,
                    "durum": "kayitli",
                    "zaman": _iso(veri.get("createdAt")),
                })
        olaylar.sort(key=lambda item: item.get("zaman") or "", reverse=True)
        return {
            "durum": "hazir",
            "olaylar": olaylar[:limit],
            # Olaylar ilk N şirketten, şirket başına en yeni kayıtlardan derlenir.
            "taranan_sirket_siniri": OLAY_TARAMA_SINIRI,
            "mesaj_icerigi_gosterilir": False,
        }
    except Exception:
        return {"durum": "veri_kaynagi_kullanilamiyor", "olaylar": [], "mesaj_icerigi_gosterilir": False}


def platform_sirket_detayi(sirket_id: str) -> dict:
    """Finans içeriğini okumadan şirketin kullanım ve destek görünümünü üretir."""
    try:
        db = _db()
        sirket_ref = db.collection("companies").document(sirket_id)
        sirket_belgesi = sirket_ref.get()
        if not sirket_belgesi.exists:
            raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
        veri = sirket_belgesi.to_dict() or {}
        profil = veri.get("profile") if isinstance(veri.get("profile"), dict) else {}

        uyeler = []
        for belge in sirket_ref.collection("members").limit(500).stream():
            uye = belge.to_dict() or {}
            uyeler.append({
                "kullanici_ozeti": _aktor_ozeti(belge.id),
                "eposta_maskeli": _eposta_maskele(uye.get("email")),
                "rol": str(uye.get("role") or "viewer")[:20],
                "eklenme": _iso(uye.get("addedAt")),
            })
        uyeler.sort(key=lambda item: (item["rol"] != "admin", item["eposta_maskeli"]))

        davetler = []
        for belge in sirket_ref.collection("invitations").limit(200).stream():
            davet = belge.to_dict() or {}
            if str(davet.get("status") or "pending") != "pending":
                continue
            davetler.append({
                "davet_ozeti": _aktor_ozeti(belge.id),
                "eposta_maskeli": _eposta_maskele(davet.get("email")),
                "rol": str(davet.get("role") or "viewer")[:20],
                "son_gecerlilik": _iso(davet.get("expiresAt")),
            })

        audit_kayitlari = []
        for belge in _son_kayitlar(sirket_ref.collection("auditLogs"), 300).stream():
            kayit = belge.to_dict() or {}
            audit_kayitlari.append(kayit)
        aktivite = _aktivite_ozeti(audit_kayitlari)
        son_olaylar = sorted(
            audit_kayitlari,
            key=lambda kayit: _datetime(kayit.get("createdAt")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )[:50]

        bildirimler = []
        for belge in sirket_ref.collection("feedback").limit(200).stream():
            bildirim = belge.to_dict() or {}
            memnuniyet = bildirim.get("satisfaction") if isinstance(bildirim.get("satisfaction"), dict) else None
            bildirimler.append({
                "geri_bildirim_id": belge.id,
                "talep_no": bildirim.get("ticketNo"),
                "kategori": str(bildirim.get("category") or "geri_bildirim")[:40],
                "sayfa": str(bildirim.get("page") or "bilinmiyor")[:80],
                "durum": str(bildirim.get("status") or "new")[:20],
                "iletisim_izni": bool(bildirim.get("contactAllowed")),
                # Mesaj gövdesi değil; yalnız yanıt verilmiş mi ve memnuniyet.
                "yanit_verildi": bool(bildirim.get("response")),
                "memnun": memnuniyet.get("satisfied") if memnuniyet else None,
                "zaman": _iso(bildirim.get("createdAt")),
            })
        bildirimler.sort(key=lambda item: item.get("zaman") or "", reverse=True)

        return {
            "durum": "hazir",
            "sirket": {
                "sirket_id": sirket_id,
                "sirket_adi": str(veri.get("name") or veri.get("companyName") or "Adsız şirket")[:160],
                "durum": _durum(veri),
                "plan": str(veri.get("plan") or "free")[:20],
                "olusturulma": _iso(veri.get("createdAt")),
                "deneme_bitis": _iso(veri.get("trialEndsAt")),
                "profil": {
                    "sektor": str(profil.get("sector") or "belirtilmedi")[:40],
                    "calisan_olcegi": str(profil.get("employeeScale") or "belirtilmedi")[:20],
                    "ana_hedef": str(profil.get("primaryGoal") or "belirtilmedi")[:40],
                    "ana_zorluk": str(profil.get("primaryChallenge") or "belirtilmedi")[:40],
                    "veri_kaynagi": str(profil.get("dataSource") or "belirtilmedi")[:40],
                    "veri_kapsami": [str(item)[:40] for item in (profil.get("availableData") or [])[:12]],
                },
            },
            "kullanim": aktivite,
            "uyeler": uyeler,
            "bekleyen_davetler": davetler,
            "geri_bildirimler": bildirimler[:50],
            "son_olaylar": [
                {
                    "aksiyon": str(kayit.get("action") or "audit")[:80],
                    "kaynak": str(kayit.get("resource") or "")[:120] or None,
                    "aktor": _aktor_ozeti(kayit.get("actorId")),
                    "aktor_rolu": str(kayit.get("actorRole") or "bilinmiyor")[:20],
                    "zaman": _iso(kayit.get("createdAt")),
                }
                for kayit in son_olaylar
            ],
            "gizlilik": {
                "finansal_veri_gosterilir": False,
                "geri_bildirim_mesaji_gosterilir": False,
                "epostalar_maskeli": True,
                "kullanici_kimlikleri_ozetlenmis": True,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Şirket işletim ayrıntıları şu anda alınamıyor.") from exc


#: platform_sayaclari örneklem başına en fazla kaç şirketi tarar.
SAYAC_ORNEKLEM_SINIRI = 100


def platform_sayaclari() -> dict:
    """Platform işletim sayaçları.

    Şirket toplamı gerçek (aggregation) sorgudan gelir; aktif/pilot/üye gibi
    kalem sayımları ise ilk N şirketlik örneklem üzerinden hesaplanır ve
    "orneklem_disi" ile açıkça etiketlenir. Örneklem toplamı aşmıyorsa (tüm
    şirketler taranmışsa) kapsam "tam"dır. Böylece panel, örneklem sayısını
    gerçek toplammış gibi sunmaz.
    """
    sirketler = platform_sirketleri(limit=SAYAC_ORNEKLEM_SINIRI)
    olaylar = platform_olaylari(limit=100)
    liste = sirketler["sirketler"]
    olay_listesi = olaylar["olaylar"]
    orneklem = len(liste)
    toplam_sirket = _toplam_sirket_sayisi()
    kesin_toplam = toplam_sirket is not None
    if not kesin_toplam:
        toplam_sirket = orneklem
    # Örneklem tüm şirketleri kapsıyorsa sayımlar tamdır; aşıyorsa örneklemdir.
    orneklem_disi = kesin_toplam and toplam_sirket > orneklem
    return {
        "olusturulma_zamani": datetime.now(timezone.utc).isoformat(),
        "veri_kaynagi": "hazir" if sirketler["durum"] == olaylar["durum"] == "hazir" else "sinirli",
        "toplam_sirket": toplam_sirket,
        "toplam_sirket_kesin": kesin_toplam,
        "orneklem_sirket": orneklem,
        "orneklem_siniri": SAYAC_ORNEKLEM_SINIRI,
        "kapsam": "orneklem" if orneklem_disi else "tam",
        # Aşağıdaki kalem sayımları örneklem (ilk N şirket) üzerindendir.
        "aktif_sirket": sum(1 for sirket in liste if sirket["durum"] == "active"),
        "pilot_sirket": sum(1 for sirket in liste if sirket["durum"] == "pilot"),
        "toplam_uye": sum(int(sirket["uye_sayisi"]) for sirket in liste),
        "yeni_geri_bildirim": sum(1 for olay in olay_listesi if olay["tur"] == "geri_bildirim" and olay["durum"] == "new"),
        "finansal_veri_gosterilir": False,
    }


def _sirket_claim_hedefi(sirket_verisi: dict) -> dict:
    """Üye claim'lerine yazılacak plan/durum/deneme değerlerini derler."""
    return {
        "plan": str(sirket_verisi.get("plan") or "free"),
        "trialEndsAt": _iso(sirket_verisi.get("trialEndsAt")),
        "status": str(sirket_verisi.get("status") or "active"),
    }


def _uye_claimini_yenile(app, uye_id: str, sirket_id: str, rol: str, hedef: dict) -> bool:
    """Bir üyenin oturumunu iptal edip claim'lerini günceller; başarıyı döner."""
    try:
        firebase_auth.revoke_refresh_tokens(uye_id, app=app)
        _claimleri_guncelle(
            uye_id, sirket_id, rol, app,
            hedef["plan"], hedef["trialEndsAt"], hedef["status"],
        )
        return True
    except Exception:
        return False


def _bekleyen_claim_kaydet(sirket_ref, uye_id: str, rol: str, hedef: dict, yonetici: KimlikBilgisi) -> None:
    """Başarısız iptali yeniden denenecek iş olarak kuyruğa yazar."""
    ref = sirket_ref.collection("bekleyenClaimGuncellemeleri").document(uye_id)
    mevcut = ref.get()
    deneme = (int((mevcut.to_dict() or {}).get("attempts", 0)) + 1) if mevcut.exists else 1
    ref.set({
        "userId": uye_id,
        "role": rol,
        "plan": hedef["plan"],
        "status": hedef["status"],
        "trialEndsAt": hedef["trialEndsAt"],
        "attempts": deneme,
        "requestedBy": yonetici.kullanici_id,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })


def platform_bekleyen_claimleri_yeniden_dene(sirket_id: str, yonetici: KimlikBilgisi) -> dict:
    """Askı/paket değişiminde iptali başarısız kalan üyeleri yeniden dener.

    Çözülen üyeler kuyruktan silinir; kalanlar bir sonraki denemeye bırakılır.
    Finans erişimi zaten güvenilir durum kontrolüyle kapalıdır; bu, üyelerin
    eski token'larını da bir an önce geçersiz kılmak içindir.
    """
    db = _db()
    sirket_ref = db.collection("companies").document(sirket_id)
    if not sirket_ref.get().exists:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    app = _firebase_uygulamasi()
    hedef = _sirket_claim_hedefi(sirket_ref.get().to_dict() or {})
    cozulen = 0
    kalan = 0
    for bekleyen in sirket_ref.collection("bekleyenClaimGuncellemeleri").limit(500).stream():
        uye = sirket_ref.collection("members").document(bekleyen.id).get()
        profil = db.collection("users").document(bekleyen.id).get()
        rol = str((uye.to_dict() or {}).get("role") or "")
        # Kuyruk geçmiş niyeti taşır; yetki kaynağı güncel üyelik ve profildir.
        if (not uye.exists or not profil.exists
                or (profil.to_dict() or {}).get("companyId") != sirket_id
                or rol not in {"admin", "cfo", "analyst", "viewer"}):
            sirket_ref.collection("bekleyenClaimGuncellemeleri").document(bekleyen.id).delete()
            continue
        if _uye_claimini_yenile(app, bekleyen.id, sirket_id, rol, hedef):
            sirket_ref.collection("bekleyenClaimGuncellemeleri").document(bekleyen.id).delete()
            cozulen += 1
        else:
            kalan += 1
    db.collection("platformAuditLogs").document().set({
        "action": "company.claims.retry",
        "companyId": sirket_id,
        "resolved": cozulen,
        "remaining": kalan,
        "actorId": yonetici.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    })
    return {
        "durum": "tamamlandi" if kalan == 0 else "kismen_tamamlandi",
        "sirket_id": sirket_id,
        "cozulen_uye": cozulen,
        "kalan_uye": kalan,
    }


def platform_sirketini_guncelle(istek: PlatformSirketGuncellemeIstegi, yonetici: KimlikBilgisi) -> dict:
    """Paket/durum değişikliğini finansal verilere dokunmadan denetim iziyle uygular."""
    db = _db()
    sirket_ref = db.collection("companies").document(istek.sirket_id)
    mevcut_belge = sirket_ref.get()
    if not mevcut_belge.exists:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    degisiklik: dict[str, Any] = {"updatedAt": firestore.SERVER_TIMESTAMP}
    if istek.durum is not None:
        degisiklik["status"] = istek.durum
        onceki_durum = _durum(mevcut_belge.to_dict() or {})
        if istek.durum == "pilot" and (onceki_durum != "pilot" or not (mevcut_belge.to_dict() or {}).get("pilotStartedAt")):
            degisiklik["pilotStartedAt"] = firestore.SERVER_TIMESTAMP
        elif istek.durum != "pilot" and onceki_durum == "pilot":
            degisiklik["pilotEndedAt"] = firestore.SERVER_TIMESTAMP
    if istek.plan is not None:
        degisiklik["plan"] = istek.plan
    batch = db.batch()
    batch.set(sirket_ref, degisiklik, merge=True)
    audit_ref = db.collection("platformAuditLogs").document()
    batch.set(audit_ref, {
        "action": "company.update",
        "companyId": istek.sirket_id,
        "changes": {key: degisiklik[key] for key in ("status", "plan") if key in degisiklik},
        "reason": " ".join(istek.gerekce.split()) if istek.gerekce else None,
        "actorId": yonetici.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    })
    batch.commit()
    basarili: list[str] = []
    basarisiz: list[str] = []
    if istek.plan is not None or istek.durum is not None:
        app = _firebase_uygulamasi()
        hedef = _sirket_claim_hedefi(sirket_ref.get().to_dict() or {})
        for uye in sirket_ref.collection("members").limit(500).stream():
            rol = str((uye.to_dict() or {}).get("role") or "viewer")
            if _uye_claimini_yenile(app, uye.id, istek.sirket_id, rol, hedef):
                basarili.append(uye.id)
                # Daha önce başarısız kalıp kuyruğa alınmışsa temizle.
                sirket_ref.collection("bekleyenClaimGuncellemeleri").document(uye.id).delete()
            else:
                # İptal başarısız oldu: üyenin eski token'ı (~1 saat) hâlâ
                # geçerli olabilir. Finans erişimi güvenilir durum kontrolüyle
                # (auth.mevcut_sirket_uyesi_dogrulanmis) zaten kapanır; burada
                # iptali yeniden denenecek iş olarak kaydediyoruz.
                basarisiz.append(uye.id)
                _bekleyen_claim_kaydet(sirket_ref, uye.id, rol, hedef, yonetici)
    return {
        "durum": "guncellendi" if not basarisiz else "kismen_guncellendi",
        "sirket_id": istek.sirket_id,
        "degisiklikler": {key: degisiklik[key] for key in ("status", "plan") if key in degisiklik},
        "basarili_uye": len(basarili),
        "basarisiz_uye": len(basarisiz),
        # Geriye dönük uyum: eski istemci bu alanı okuyor.
        "oturum_yenileme_uyarisi": len(basarisiz),
        "yeniden_denenecek_uye": len(basarisiz),
    }


def platform_sirket_eylemi(istek: PlatformSirketEylemIstegi, yonetici: KimlikBilgisi) -> dict:
    """Yüksek etkili platform eylemlerini gerekçe ve denetim iziyle uygular."""
    db = _db()
    sirket_ref = db.collection("companies").document(istek.sirket_id)
    if not sirket_ref.get().exists:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    if istek.eylem != "oturumlari_sonlandir":
        raise HTTPException(status_code=422, detail="Platform eylemi desteklenmiyor.")

    app = _firebase_uygulamasi()
    basarili = 0
    hatali = 0
    for uye in sirket_ref.collection("members").limit(500).stream():
        try:
            firebase_auth.revoke_refresh_tokens(uye.id, app=app)
            basarili += 1
        except Exception:
            hatali += 1
    db.collection("platformAuditLogs").document().set({
        "action": "company.sessions.revoke",
        "companyId": istek.sirket_id,
        "reason": " ".join(istek.gerekce.split()),
        "affectedUsers": basarili,
        "failedUsers": hatali,
        "actorId": yonetici.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    })
    return {
        "durum": "tamamlandi" if hatali == 0 else "kismen_tamamlandi",
        "sirket_id": istek.sirket_id,
        "eylem": istek.eylem,
        "etkilenen_kullanici": basarili,
        "basarisiz_kullanici": hatali,
    }


def platform_geri_bildirim_durumu(
    istek: PlatformGeriBildirimDurumIstegi,
    yonetici: KimlikBilgisi,
) -> dict:
    """Mesaj içeriğini okumadan geri bildirim iş akışı durumunu yönetir."""
    db = _db()
    sirket_ref = db.collection("companies").document(istek.sirket_id)
    if not sirket_ref.get().exists:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    bildirim_ref = sirket_ref.collection("feedback").document(istek.geri_bildirim_id)
    if not bildirim_ref.get().exists:
        raise HTTPException(status_code=404, detail="Geri bildirim bulunamadı.")
    guncelleme: dict[str, Any] = {
        "status": istek.durum,
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "updatedByPlatform": yonetici.kullanici_id,
    }
    # Yönetici, mesaj gövdesini okumadan da müşteriye görünecek kısa bir
    # yanıt bırakabilir. Bu yanıt talebi açan kullanıcıya gösterilir.
    if istek.yanit:
        guncelleme["response"] = " ".join(istek.yanit.split())
        guncelleme["respondedAt"] = firestore.SERVER_TIMESTAMP
        guncelleme["respondedByPlatform"] = yonetici.kullanici_id
    batch = db.batch()
    batch.set(bildirim_ref, guncelleme, merge=True)
    batch.set(db.collection("platformAuditLogs").document(), {
        "action": "feedback.status_update",
        "companyId": istek.sirket_id,
        "feedbackId": istek.geri_bildirim_id,
        "status": istek.durum,
        "reason": " ".join(istek.gerekce.split()) if istek.gerekce else None,
        "actorId": yonetici.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    })
    batch.commit()
    return {
        "durum": "guncellendi",
        "sirket_id": istek.sirket_id,
        "geri_bildirim_id": istek.geri_bildirim_id,
        "geri_bildirim_durumu": istek.durum,
    }
