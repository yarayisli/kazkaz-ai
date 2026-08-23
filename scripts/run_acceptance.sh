#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

if [[ ! -x ".venv/bin/python" ]]; then
  echo ".venv/bin/python bulunamadı; önce requirements-api.txt bağımlılıklarını kurun." >&2
  exit 2
fi

echo "[1/6] Backend ve güvenlik testleri"
.venv/bin/python -m unittest discover -s api/tests -v

echo "[2/6] Finans motoru regresyon testleri"
.venv/bin/python -m unittest test_engines -v

echo "[3/6] Python sözdizimi kontrolü"
.venv/bin/python -m compileall -q api cfo_agent.py gemini_engine.py

echo "[4/6] Frontend tip ve üretim derlemesi"
npm --prefix web run lint
npm --prefix web run build

echo "[5/6] Frontend bağımlılık güvenliği"
npm --prefix web audit --omit=dev --audit-level=high

echo "[6/6] Depo gizli anahtar kontrolü"
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
