"""Şirket kapsamlı, sınırlı ve denetlenebilir kullanıcı geri bildirimi kaydı."""

from firebase_admin import firestore

from api.auth import _firebase_uygulamasi
from api.models import GeriBildirimIstegi, KimlikBilgisi


def geri_bildirim_kaydet(istek: GeriBildirimIstegi, kullanici: KimlikBilgisi) -> dict:
    app = _firebase_uygulamasi()
    db = firestore.client(app=app)
    belge = db.collection("companies").document(kullanici.sirket_id).collection("feedback").document()
    belge.set({
        "category": istek.kategori,
        "message": " ".join(istek.mesaj.split()),
        "page": istek.sayfa,
        "contactAllowed": istek.iletisim_izni,
        "createdBy": kullanici.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "status": "new",
    })
    return {"durum": "alindi", "kayit_id": belge.id}
