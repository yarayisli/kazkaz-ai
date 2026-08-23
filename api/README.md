# KazKaz AI V1 API

Mevcut Python finans motorlarını React istemcisine açan güvenli FastAPI katmanıdır.

## Yerel çalıştırma

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
uvicorn api.main:uygulama --reload --port 8000
```

Varsayılan olarak korumalı uçlar Firebase ID token ister. Sadece yerel geliştirmede
`KAZKAZ_AUTH_DISABLED=true` kullanılabilir; bu seçenek `APP_ENV=production` iken
kimlik doğrulamayı devre dışı bırakmaz.

## Uçlar

- `GET /api/health`
- `GET /api/v1/oturum`
- `POST /api/v1/finans/denetim`
- `POST /api/v1/finans/zaman-serisi`
- `POST /api/v1/cfo/sohbet`
