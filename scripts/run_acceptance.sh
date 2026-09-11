#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

if [[ ! -x ".venv/bin/python" ]]; then
  echo ".venv/bin/python bulunamadı; önce requirements-api.txt bağımlılıklarını kurun." >&2
  exit 2
fi

echo "[1/8] Backend ve güvenlik testleri"
.venv/bin/python -m unittest discover -s api/tests -v

echo "[2/8] Finans motoru ve kullanım sayacı regresyon testleri"
.venv/bin/python -m unittest test_engines test_usage_tracker -v

echo "[3/8] Python sözdizimi kontrolü"
.venv/bin/python -m compileall -q api cfo_agent.py gemini_engine.py

echo "[4/8] Frontend davranış testleri"
npm --prefix web test

echo "[5/8] Frontend tip ve üretim derlemesi"
npm --prefix web run lint
npm --prefix web run build

echo "[6/8] Masaüstü ve mobil tarayıcı kabul testleri"
npm --prefix web run test:e2e

echo "[7/8] Frontend bağımlılık güvenliği"
npm --prefix web audit --omit=dev --audit-level=high

echo "[8/8] Depo gizli anahtar kontrolü"
if git ls-files | rg -i '(^|/)(\.env|.*firebase-adminsdk.*\.json|firebase-key\.json|.*service-account.*\.json|.*\.pem|.*\.key)$'; then
  echo "Gizli değer taşıyabilecek dosya Git tarafından izleniyor." >&2
  exit 3
fi
if rg -l --hidden \
  -g '!.git/**' -g '!.venv/**' -g '!venv/**' -g '!web/node_modules/**' \
  -g '!web/dist/**' -g '!api/tests/**' -g '!.env' -g '!.env.*' \
  '(nvapi-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)' .; then
  echo "Olası gerçek gizli anahtar bulundu; kabul turu durduruldu." >&2
  exit 3
fi

echo "Yerel teknik kabul kapısı başarılı. Canlı Firebase, yedek geri yükleme ve uzman onayları ayrıca tamamlanmalıdır."
