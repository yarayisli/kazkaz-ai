#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-https://supermantarik.com}"
if [[ "$base_url" != https://* ]]; then
  echo "Smoke test yalnız HTTPS adresinde çalışır." >&2
  exit 2
fi

base_url="${base_url%/}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl --fail --silent --show-error --proto '=https' --tlsv1.2 --max-time 20 \
  --dump-header "$tmp_dir/headers" "$base_url/api/health" --output "$tmp_dir/health.json"

rg -q '"durum"\s*:\s*"ok"' "$tmp_dir/health.json"
rg -qi '^strict-transport-security:\s*max-age=' "$tmp_dir/headers"
rg -qi '^x-content-type-options:\s*nosniff' "$tmp_dir/headers"
rg -qi '^content-security-policy:' "$tmp_dir/headers"
rg -qi '^x-request-id:\s*[A-Za-z0-9_-]{8,64}' "$tmp_dir/headers"

curl --fail --silent --show-error --proto '=https' --tlsv1.2 --max-time 20 \
  "$base_url/api/readiness" --output "$tmp_dir/readiness.json"
rg -q '"kritik_kontroller"' "$tmp_dir/readiness.json"
rg -q '"https_zorunlu"\s*:\s*true' "$tmp_dir/readiness.json"
rg -q '"izinli_hostlar"\s*:\s*true' "$tmp_dir/readiness.json"

curl --fail --silent --show-error --proto '=https' --tlsv1.2 --max-time 20 \
  "$base_url/api/public/performance" --output "$tmp_dir/performance.json"
rg -q '"kisisel_veri_toplanir"\s*:\s*false' "$tmp_dir/performance.json"

http_url="http://${base_url#https://}"
redirect_headers="$(curl --silent --show-error --max-time 20 --head "$http_url/api/health")"
printf '%s' "$redirect_headers" | rg -qi '^location:\s*https://'

echo "HTTPS, TLS, yönlendirme, güvenlik başlıkları ve operasyon uçları başarılı: $base_url"
