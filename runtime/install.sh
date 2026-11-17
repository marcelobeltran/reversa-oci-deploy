#!/usr/bin/env bash
set -euo pipefail
umask 022
export DEBIAN_FRONTEND=noninteractive
# Ubuntu's default archive URLs are HTTP; keep VM egress restricted to HTTPS.
sed -i 's|http://|https://|g' /etc/apt/sources.list.d/ubuntu.sources
apt-get update
apt-get install -y nginx apache2-utils nodejs npm python3-venv curl ca-certificates iptables-persistent
LB_CIDR=$(python3 -c 'import json;print(json.load(open("/etc/reversa/config.json"))["lb_subnet_cidr"])')
# OCI Ubuntu images can ship an INPUT reject rule. Permit only the LB subnet.
for PORT in 80 443; do
  iptables -C INPUT -p tcp -s "$LB_CIDR" --dport "$PORT" -j ACCEPT 2>/dev/null || \
    iptables -I INPUT 1 -p tcp -s "$LB_CIDR" --dport "$PORT" -j ACCEPT
done
if command -v netfilter-persistent >/dev/null; then netfilter-persistent save; fi
id opc >/dev/null 2>&1 || useradd --create-home --shell /bin/bash opc
install -d -o opc -g opc -m 0700 /home/opc/proyectos /home/opc/.config/opencode /home/opc/.config/reversa-portal
python3 -m venv /opt/reversa/venv
/opt/reversa/venv/bin/pip install --disable-pip-version-check -r /opt/reversa/requirements.txt
OPENCODE_VERSION=$(python3 -c 'import json;print(json.load(open("/etc/reversa/config.json"))["opencode_version"])')
CERTBOT_VERSION=$(python3 -c 'import json;print(json.load(open("/etc/reversa/config.json"))["certbot_version"])')
npm install --global "opencode-ai@$OPENCODE_VERSION" reversa@1.3.4
python3 -m venv /opt/reversa/certbot
/opt/reversa/certbot/bin/pip install --disable-pip-version-check "certbot==$CERTBOT_VERSION"
install -m 0755 /opt/reversa/project_init.mjs /usr/local/bin/reversa-project-init
# The portal initializer invokes /usr/bin/npm on Ubuntu, the source's audited path.
install -d -m 0755 /var/www/reversa-acme/.well-known/acme-challenge
/opt/reversa/venv/bin/python /opt/reversa/configure.py
install -m 0644 /opt/reversa/nginx-http.conf /etc/nginx/sites-available/reversa
ln -sfn /etc/nginx/sites-available/reversa /etc/nginx/sites-enabled/reversa
if [ -L /etc/nginx/sites-enabled/default ]; then unlink /etc/nginx/sites-enabled/default; fi
nginx -t
systemctl enable nginx
systemctl restart nginx
install -m 0644 /opt/reversa/systemd/* /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now reversa-opencode.service reversa-portal.service reversa-certificate.timer
systemctl start --no-block reversa-certificate.service
echo 'Reversa bootstrap instalado. Comprobar TLS y pruebas funcionales antes de declarar listo.'
