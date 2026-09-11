"""Şirket kapsamlı, sınırlı ve denetlenebilir kullanıcı geri bildirimi kaydı.

Destek döngüsü müşteri tarafında da kapanır: kullanıcı bir talep numarası alır,
kendi taleplerinin durumunu ve varsa yöneticinin kısa yanıtını görebilir ve
talep çözüldüğünde kısa bir memnuniyet işareti bırakabilir. "Çözüldü" işareti
tek başına çözüm kanıtı sayılmaz; memnuniyet ayrı ölçülür.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException, status
from firebase_admin import firestore

from api.auth import _firebase_uygulamasi
from api.models import GeriBildirimIstegi, GeriBildirimMemnuniyetIstegi, KimlikBilgisi


def _db():
    return firestore.client(app=_firebase_uygulamasi())


def _talep_no(belge_id: str) -> str:
    """Doküman kimliğinden kullanıcıya gösterilecek kısa, okunabilir talep no."""
    return "T-" + belge_id[-6:].upper()


def _iso(deger: Any) -> Any:
    return deger.isoformat() if hasattr(deger, "isoformat") else deger


def geri_bildirim_kaydet(istek: GeriBildirimIstegi, kullanici: KimlikBilgisi) -> dict:
    db = _db()
    belge = db.collection("companies").document(kullanici.sirket_id).collection("feedback").document()
    talep_no = _talep_no(belge.id)
    belge.set({
        "ticketNo": talep_no,
        "category": istek.kategori,
        "message": " ".join(istek.mesaj.split()),
        "page": istek.sayfa,
        "contactAllowed": istek.iletisim_izni,
        "createdBy": kullanici.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "status": "new",
    })
    return {"durum": "alindi", "kayit_id": belge.id, "talep_no": talep_no}


def geri_bildirimlerim(kullanici: KimlikBilgisi) -> Dict[str, Any]:
    """Kullanıcının kendi taleplerini durum ve yönetici yanıtıyla döner.

    Yalnız çağıranın açtığı talepler döner (createdBy eşleşmesi); başkasının
    talebi gösterilmez. Mesaj gövdesi kullanıcının kendi yazdığı metindir.
    """
    if not kullanici.sirket_id:
        return {"talepler": []}
    db = _db()
    koleksiyon = db.collection("companies").document(str(kullanici.sirket_id)).collection("feedback")
    talepler = []
    for belge in koleksiyon.stream():
        veri = belge.to_dict() or {}
        if veri.get("createdBy") != kullanici.kullanici_id:
            continue
        memnuniyet = veri.get("satisfaction") if isinstance(veri.get("satisfaction"), dict) else None
        talepler.append({
            "geri_bildirim_id": belge.id,
            "talep_no": veri.get("ticketNo") or _talep_no(belge.id),
            "kategori": veri.get("category"),
            "sayfa": veri.get("page"),
            "mesaj": veri.get("message"),
            "durum": veri.get("status", "new"),
            "yanit": veri.get("response"),
            "olusturma": _iso(veri.get("createdAt")),
            "guncelleme": _iso(veri.get("updatedAt")),
            "memnun": memnuniyet.get("satisfied") if memnuniyet else None,
        })
    talepler.sort(key=lambda t: str(t.get("olusturma") or ""), reverse=True)
    return {"talepler": talepler[:50]}


def geri_bildirim_memnuniyeti(istek: GeriBildirimMemnuniyetIstegi, kullanici: KimlikBilgisi) -> Dict[str, Any]:
    """Çözülmüş bir talep için memnuniyet işareti kaydeder.

    Yalnız talebi açan kullanıcı ve yalnız 'resolved' durumundaki talep için
    kabul edilir — kapanmamış bir işe memnuniyet iliştirilmez.
    """
    db = _db()
    belge_ref = (
        db.collection("companies").document(str(kullanici.sirket_id))
        .collection("feedback").document(istek.geri_bildirim_id)
    )
    belge = belge_ref.get()
    if not belge.exists:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")
    veri = belge.to_dict() or {}
    if veri.get("createdBy") != kullanici.kullanici_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu talep size ait değil.")
    if veri.get("status") != "resolved":
        raise HTTPException(status_code=409, detail="Memnuniyet yalnız çözülmüş talep için verilebilir.")
    yeniden_acildi = not bool(istek.memnun)
    guncelleme = {
        "satisfaction": {
            "satisfied": bool(istek.memnun),
            "at": firestore.SERVER_TIMESTAMP,
            "by": kullanici.kullanici_id,
        },
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    if yeniden_acildi:
        # Kullanıcı “çözülmedi” dediğinde talebi yalnız ölçmekle kalma; destek
        # kuyruğuna geri al. Önceki yanıt denetim izi olarak korunur.
        guncelleme.update({
            "status": "in_review",
            "reopenedAt": firestore.SERVER_TIMESTAMP,
            "reopenedBy": kullanici.kullanici_id,
        })
    belge_ref.set(guncelleme, merge=True)
    return {
        "durum": "yeniden_acildi" if yeniden_acildi else "kaydedildi",
        "talep_no": veri.get("ticketNo") or _talep_no(belge.id),
        "memnun": bool(istek.memnun),
        "talep_durumu": "in_review" if yeniden_acildi else "resolved",
    }
