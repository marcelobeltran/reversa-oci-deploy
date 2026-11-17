#!/usr/bin/env bash
set -euo pipefail
exec 9>/run/reversa-certificate.lock
flock -n 9 || exit 0
IP=$(python3 -c 'import json;print(json.load(open("/etc/reversa/config.json"))["public_ip"])')
CERTBOT=/opt/reversa/certbot/bin/certbot
if [ ! -s /etc/letsencrypt/live/reversa/fullchain.pem ]; then
  "$CERTBOT" certonly --non-interactive --agree-tos --register-unsafely-without-email \
    --preferred-profile shortlived --webroot -w /var/www/reversa-acme \
    --ip-address "$IP" --cert-name reversa
else
  "$CERTBOT" renew --non-interactive --cert-name reversa
fi
# Atomically build config after a trusted certificate exists. No temporary self-signed endpoint.
cat /opt/reversa/nginx-http.conf /opt/reversa/nginx-https.conf > /etc/nginx/sites-available/reversa.candidate
cp /etc/nginx/sites-available/reversa /etc/nginx/sites-available/reversa.previous
mv /etc/nginx/sites-available/reversa.candidate /etc/nginx/sites-available/reversa
if nginx -t; then
  systemctl reload nginx
  echo 'Certificado Reversa válido cargado'
else
  mv /etc/nginx/sites-available/reversa.previous /etc/nginx/sites-available/reversa
  exit 1
fi
