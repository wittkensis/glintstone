#!/bin/sh
# Glintstone v2 — VPS Provisioning (Hostinger, Alpine Linux)
# Run on a fresh Alpine VPS: ssh root@YOUR_VPS_IP 'sh -s' < ops/deploy/provision.sh
#
# Specs: 8GB RAM, 100GB storage, 2 CPU cores
# Installs: nginx, Python 3, PostgreSQL 17, supervisor, certbot
#
# Firewall: Handled by Hostinger hPanel (not OS-level). Ensure ports 22, 80, 443 are open.
set -e

DOMAIN="glintstone.org"
DB_NAME="glintstone"
DB_USER="glintstone"
DB_PASS="$(head -c 32 /dev/urandom | base64 | tr -d '=+/')"
DEPLOY_USER="deploy"
APP_DIR="/var/www/glintstone"

echo "=== Glintstone VPS Provisioning (Alpine / Hostinger) ==="

# --- System packages ---
apk update && apk upgrade

apk add \
    nginx \
    postgresql17 postgresql17-client \
    python3 py3-pip py3-virtualenv \
    supervisor \
    certbot certbot-nginx \
    sudo \
    curl git rsync openssh

# --- Disable OS-level firewall (using Hostinger hPanel firewall instead) ---
# Alpine uses iptables by default; clear any rules to avoid double-firewall issues
if command -v iptables &> /dev/null; then
    iptables -F 2>/dev/null || true
    iptables -P INPUT ACCEPT 2>/dev/null || true
    iptables -P FORWARD ACCEPT 2>/dev/null || true
    iptables -P OUTPUT ACCEPT 2>/dev/null || true
fi

# --- PostgreSQL ---
if [ ! -d /var/lib/postgresql/17/data ]; then
    mkdir -p /var/lib/postgresql/17/data
    chown postgres:postgres /var/lib/postgresql/17/data
    su - postgres -c "initdb -D /var/lib/postgresql/17/data"
fi

rc-update add postgresql default
rc-service postgresql start

su - postgres -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\"" 2>/dev/null || true
su - postgres -c "psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\"" 2>/dev/null || true

# --- Deploy user ---
adduser -D -s /bin/sh "$DEPLOY_USER" 2>/dev/null || true

# Unlock account for SSH key auth (Alpine locks passwordless accounts by default)
sed -i "s/^${DEPLOY_USER}:!/${DEPLOY_USER}:*/" /etc/shadow

mkdir -p "/home/$DEPLOY_USER/.ssh"
if [ -f /root/.ssh/authorized_keys ]; then
    cp /root/.ssh/authorized_keys "/home/$DEPLOY_USER/.ssh/"
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
    chmod 700 "/home/$DEPLOY_USER/.ssh"
    chmod 600 "/home/$DEPLOY_USER/.ssh/authorized_keys"
fi

# Allow deploy user to restart services without password
cat > /etc/sudoers.d/glintstone << 'SUDOERS'
deploy ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl restart glintstone-*
deploy ALL=(ALL) NOPASSWD: /sbin/rc-service nginx reload
deploy ALL=(ALL) NOPASSWD: /bin/cp * /etc/nginx/http.d/*
SUDOERS
chmod 440 /etc/sudoers.d/glintstone

# --- App directory ---
mkdir -p "$APP_DIR"
chown "$DEPLOY_USER:$DEPLOY_USER" "$APP_DIR"

# --- Python virtual environment ---
su - "$DEPLOY_USER" -c "python3 -m venv $APP_DIR/venv"

# --- Supervisor config for uvicorn processes ---
mkdir -p /etc/supervisor.d

cat > /etc/supervisor.d/glintstone-api.ini << 'SUPERVISOR'
[program:glintstone-api]
command=/var/www/glintstone/venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8001
directory=/var/www/glintstone
user=deploy
autostart=true
autorestart=true
stderr_logfile=/var/log/glintstone-api.err.log
stdout_logfile=/var/log/glintstone-api.out.log
SUPERVISOR

cat > /etc/supervisor.d/glintstone-web.ini << 'SUPERVISOR'
[program:glintstone-web]
command=/var/www/glintstone/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8002
directory=/var/www/glintstone
user=deploy
autostart=true
autorestart=true
stderr_logfile=/var/log/glintstone-web.err.log
stdout_logfile=/var/log/glintstone-web.out.log
SUPERVISOR

# --- Services ---
rc-update add nginx default
rc-update add supervisord default
rc-update add sshd default

rc-service supervisord start
rc-service nginx start

echo ""
echo "=========================================="
echo "  Provisioning complete"
echo "=========================================="
echo ""
echo "  DB_USER: $DB_USER"
echo "  DB_PASS: $DB_PASS"
echo ""
echo "  SAVE THIS PASSWORD NOW."
echo ""
echo "  Next steps:"
echo "    1. In Hostinger hPanel: create firewall group with ports 22, 80, 443"
echo "    2. Point DNS A records: glintstone.org, api.glintstone.org, app.glintstone.org -> this VPS"
echo "    3. Create $APP_DIR/.env with production values (see ops/deploy/DEPLOY.md)"
echo "    4. From local machine: ./ops/deploy/deploy.sh"
echo "    5. SSL: certbot --nginx -d glintstone.org -d api.glintstone.org -d app.glintstone.org"
echo ""
