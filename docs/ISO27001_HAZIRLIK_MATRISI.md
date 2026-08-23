# ISO/IEC 27001 hazırlık matrisi

Bu matris sertifika değildir. Sertifikasyon kapsamı, risk işleme planı, iç denetim
ve akredite belgelendirme kuruluşu denetimi tamamlanmadan KazKaz AI “ISO 27001
sertifikalı” olarak tanıtılamaz.

| Kontrol alanı | Mevcut teknik kanıt | Açık iş | Sorumlu/Onay |
|---|---|---|---|
| Varlık envanteri | Repo, Firebase, AI ve deploy değişkenleri listeli | Sahip ve sınıflandırma kaydı | Güvenlik |
| Kimlik ve erişim | Firebase token, şirket üyeliği, dört rol | Periyodik erişim gözden geçirme | Güvenlik + yönetim |
| Tenant izolasyonu | Backend tenant yolları, Firestore kuralları, birim testleri | Emulator/canlı saldırı testi | Güvenlik |
| Kriptografi | Secret env yaklaşımı, üretim HTTPS/HSTS hazırlığı | Canlı TLS ve anahtar rotasyonu kanıtı | DevOps |
| Güvenli geliştirme | 156 test, tip kontrolü, gizli anahtar taraması | Bağımlılık/SAST bulgu SLA’sı | Yazılım |
| Olay yönetimi | Sentry yapılandırma noktası, request ID | Çağrı zinciri ve tatbikat | Operasyon |
| Yedekleme | Export/restore drill scriptleri | Ayrı proje tatbikatı ve RPO/RTO | DevOps |
| Tedarikçi güvenliği | Sağlayıcılar env ile ayrılmış | DPA, veri bölgesi, yıllık gözden geçirme | Hukuk + güvenlik |
| İş sürekliliği | Tek servis Docker/Render planı | Bölgesel kesinti ve geri dönüş planı | Yönetim |
| Log ve izleme | Anonim performans, Sentry, request ID | Merkezi log saklama ve alarm eşikleri | Operasyon |
| Veri yaşam döngüsü | Export/silme, retention alanları | TTL ve yedek lifecycle canlı kanıtı | Hukuk + DevOps |
| İnsan kaynakları | Teknik rol matrisi | Gizlilik, ayrılış ve farkındalık prosedürü | Yönetim |

## Sertifikasyon kapısı

- [ ] BGYS kapsamı ve hariç tutulan varlıklar yazıldı.
- [ ] Risk metodolojisi ve risk kayıtları yönetimce onaylandı.
- [ ] Uygulanabilirlik Bildirgesi (SoA) hazırlandı.
- [ ] Politikalar yürürlüğe alındı ve personele duyuruldu.
- [ ] Kanıtlar en az bir işletim döngüsü boyunca toplandı.
- [ ] İç denetim bulguları kapatıldı.
- [ ] Yönetimin gözden geçirmesi tamamlandı.
- [ ] Aşama 1 ve Aşama 2 denetimleri başarıyla tamamlandı.
- [ ] Sertifika numarası, kapsamı, kuruluşu ve geçerlilik tarihi doğrulandı.
