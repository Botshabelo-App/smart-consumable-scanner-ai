#!/usr/bin/env bash
# One-time / idempotent production setup on an Ubuntu DigitalOcean Droplet.
# Usage (as root): DOMAIN=api.example.co.za bash deploy/server-setup.sh
set -euo pipefail
: "${DOMAIN:?DOMAIN is required}"
APP_DIR=/opt/smart-consumable-scanner-ai
BRANCH=${BRANCH:-production/v1}

if ! command -v docker >/dev/null; then
  apt-get update -y && apt-get install -y ca-certificates curl git ufw
  curl -fsSL https://get.docker.com | sh
fi
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable

if [ ! -f /swapfile ] && [ "$(free -m | awk '/Mem:/{print $2}')" -lt 4000 ]; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

if [ "${SKIP_GIT:-0}" = "1" ]; then
  echo "SKIP_GIT=1: using code already in $APP_DIR"
elif [ ! -d "$APP_DIR/.git" ]; then
  git clone -b "$BRANCH" https://github.com/Botshabelo-App/smart-consumable-scanner-ai.git "$APP_DIR"
else
  git -C "$APP_DIR" fetch origin "$BRANCH" && git -C "$APP_DIR" checkout "$BRANCH" && git -C "$APP_DIR" reset --hard "origin/$BRANCH"
fi
cd "$APP_DIR"

if [ ! -f .env ]; then
  umask 077
  cat > .env <<ENV
DOMAIN=$DOMAIN
POSTGRES_PASSWORD=$(openssl rand -hex 24)
SECRET_KEY=$(openssl rand -hex 32)
ENV
fi
sed -i "s/^DOMAIN=.*/DOMAIN=$DOMAIN/" .env

cat > /etc/systemd/system/smart-scanner.service <<UNIT
[Unit]
Description=Smart Consumable Scanner AI (docker compose)
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=1800

[Install]
WantedBy=multi-user.target
UNIT

mkdir -p /var/backups/smart-scanner
cat > /etc/cron.d/smart-scanner-backup <<CRON
15 2 * * * root cd $APP_DIR && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U scanner consumable_scanner | gzip > /var/backups/smart-scanner/db-\$(date +\%F).sql.gz && find /var/backups/smart-scanner -name 'db-*.sql.gz' -mtime +14 -delete
*/5 * * * * root curl -fsS -m 10 https://$DOMAIN/health >/dev/null || (logger -t smart-scanner "health check failed; restarting"; cd $APP_DIR && docker compose -f docker-compose.prod.yml up -d)
CRON

systemctl daemon-reload
systemctl enable smart-scanner.service
systemctl restart smart-scanner.service
docker compose -f docker-compose.prod.yml ps
