#!/usr/bin/env bash
# One-time staging environment bootstrap on the Hostinger VPS.
# Run AS ROOT on the VPS:
#
#   ssh root@76.13.208.149 'bash -s' < ops/deploy/provision-staging.sh
#
# Idempotent: re-running is safe. Creates only what's missing.

set -euo pipefail

APP_DIR="/var/www/glintstone-staging"
DEPLOY_USER="deploy"
STAGING_DB="glintstone_staging"
PROD_BACKUPS="/var/www/glintstone/shared/backups"

# Sanity: this script assumes production is already provisioned.
if [ ! -d /var/www/glintstone ]; then
    echo "::error:: /var/www/glintstone not found — production-side provisioning must come first." >&2
    exit 1
fi

echo "=== Staging bootstrap ==="

# --- App directory ---
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR/releases" "$APP_DIR/shared/backups"
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "$APP_DIR"
    echo "  created $APP_DIR"
else
    echo "  $APP_DIR exists"
fi

# --- Postgres role + DB ---
if ! su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='$STAGING_DB'\"" | grep -q 1; then
    su - postgres -c "psql -c \"CREATE DATABASE $STAGING_DB OWNER wittkensis;\""
    su - postgres -c "psql -d $STAGING_DB -c \"GRANT CONNECT ON DATABASE $STAGING_DB TO glintstone;\""
    su - postgres -c "psql -d $STAGING_DB -c \"GRANT USAGE ON SCHEMA public TO glintstone;\""
    su - postgres -c "psql -d $STAGING_DB -c \"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO glintstone;\""
    su - postgres -c "psql -d $STAGING_DB -c \"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO glintstone;\""
    su - postgres -c "psql -d $STAGING_DB -c \"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO glintstone;\""
    su - postgres -c "psql -d $STAGING_DB -c \"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO glintstone;\""
    echo "  created Postgres DB $STAGING_DB"
else
    echo "  Postgres DB $STAGING_DB exists"
fi

# --- shared/.env ---
if [ ! -f "$APP_DIR/shared/.env" ]; then
    if [ ! -f /var/www/glintstone/shared/.env ]; then
        echo "::error:: production .env missing — cannot derive staging .env" >&2
        exit 1
    fi
    # Copy the prod .env then rewrite the DB URLs + APP_ENV.
    sed -E \
        -e "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://glintstone@127.0.0.1:5432/$STAGING_DB|" \
        -e "s|^DATABASE_URL_MIGRATIONS=.*|DATABASE_URL_MIGRATIONS=postgresql://wittkensis@127.0.0.1:5432/$STAGING_DB|" \
        -e "s|^APP_ENV=.*|APP_ENV=staging|" \
        /var/www/glintstone/shared/.env > "$APP_DIR/shared/.env"

    # If APP_ENV wasn't in prod .env (unlikely), append it.
    grep -q '^APP_ENV=' "$APP_DIR/shared/.env" || echo "APP_ENV=staging" >> "$APP_DIR/shared/.env"

    chown "$DEPLOY_USER:$DEPLOY_USER" "$APP_DIR/shared/.env"
    chmod 600 "$APP_DIR/shared/.env"
    echo "  created $APP_DIR/shared/.env (derived from production)"
else
    echo "  $APP_DIR/shared/.env exists — leaving as-is"
fi

# --- Supervisor configs ---
for svc in api web; do
    cfg="/etc/supervisor.d/glintstone-staging-${svc}.ini"
    if [ ! -f "$cfg" ]; then
        if [ "$svc" = "api" ]; then
            port=8003
            mod="api.main:app"
            logname="glintstone-staging-api"
        else
            port=8004
            mod="app.main:app"
            logname="glintstone-staging-web"
        fi
        cat > "$cfg" <<SUP
[program:glintstone-staging-${svc}]
command=$APP_DIR/current/venv/bin/uvicorn $mod --host 127.0.0.1 --port $port
directory=$APP_DIR/current
user=$DEPLOY_USER
autostart=false
autorestart=true
environment=HOME="/home/$DEPLOY_USER",APP_ENV="staging"
stderr_logfile=/var/log/$logname.err.log
stdout_logfile=/var/log/$logname.out.log
SUP
        echo "  wrote $cfg"
    else
        echo "  $cfg exists"
    fi
done
supervisorctl reread >/dev/null
supervisorctl update >/dev/null

# --- nginx vhost (HTTP only here; certbot will rewrite for HTTPS) ---
NGINX_CFG="/etc/nginx/http.d/staging.glintstone.org.conf"
if [ ! -f "$NGINX_CFG" ]; then
    cat > "$NGINX_CFG" <<'NGINX'
server {
    listen 80;
    server_name staging.glintstone.org;

    location / {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/glintstone-staging/current/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

server {
    listen 80;
    server_name staging-api.glintstone.org;

    location / {
        proxy_pass http://127.0.0.1:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
    echo "  wrote $NGINX_CFG"
else
    echo "  $NGINX_CFG exists"
fi

if nginx -t 2>/dev/null; then
    rc-service nginx reload
    echo "  nginx reloaded"
else
    echo "::warning:: nginx -t failed — leaving running config alone" >&2
fi

# --- TLS: Let's Encrypt via certbot ---
if [ ! -d /etc/letsencrypt/live/staging.glintstone.org ]; then
    echo "  requesting Let's Encrypt cert (this requires DNS A records to be live)"
    if ! certbot --nginx --non-interactive --agree-tos \
            -m eric.wittke@gmail.com \
            -d staging.glintstone.org \
            -d staging-api.glintstone.org; then
        cat <<EOF >&2
::warning:: certbot failed. Most likely the DNS A records for
staging.glintstone.org / staging-api.glintstone.org haven't propagated yet.
Re-run this script after DNS is live, or run:
    certbot --nginx -d staging.glintstone.org -d staging-api.glintstone.org
EOF
    fi
else
    echo "  Let's Encrypt cert exists"
fi

# --- Nightly prod → staging restore cron ---
CRON_FILE="/etc/periodic/daily/glintstone-staging-restore"
if [ ! -f "$CRON_FILE" ]; then
    cat > "$CRON_FILE" <<RESTORE
#!/bin/sh
# Restore last night's prod backup into the staging DB.
# Runs as root via Alpine's /etc/periodic/daily (~03:00 by default; adjust with crontab if needed).
set -e
LOG=/var/log/glintstone-staging-restore.log
LOCK=/var/run/glintstone-staging-restore.lock
exec >>"\$LOG" 2>&1
echo "--- \$(date -u +%Y-%m-%dT%H:%M:%SZ) start ---"

# Single-instance lock: skip if another restore (or a staging deploy holding it) is mid-flight.
exec 9>"\$LOCK"
if ! flock -n 9; then
    echo "another restore is running, skipping"
    exit 0
fi

LATEST=\$(ls -1t $PROD_BACKUPS/glintstone-*.dump.gz 2>/dev/null | head -1)
if [ -z "\$LATEST" ]; then
    echo "no prod backup found; aborting"
    exit 1
fi
echo "restoring from \$LATEST"

su - postgres -c "psql -c 'DROP DATABASE IF EXISTS $STAGING_DB WITH (FORCE);'"
su - postgres -c "psql -c 'CREATE DATABASE $STAGING_DB OWNER wittkensis;'"
gunzip -c "\$LATEST" | su - postgres -c "pg_restore --jobs=2 --no-owner --role=wittkensis -d $STAGING_DB"
su - postgres -c "psql -d $STAGING_DB -c \"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO glintstone;\""
su - postgres -c "psql -d $STAGING_DB -c \"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO glintstone;\""
echo "restore done"

# Bounce staging services so they pick up the refreshed DB cleanly.
supervisorctl restart glintstone-staging-api glintstone-staging-web 2>/dev/null || true
RESTORE
    chmod +x "$CRON_FILE"
    echo "  installed $CRON_FILE"
else
    echo "  $CRON_FILE exists"
fi

# --- Sudo allowlist update (staging supervisor + nginx already covered by glintstone-* wildcard) ---
echo
echo "=== Staging bootstrap complete ==="
echo "  Next: push to staging branch to deploy the first staging release."
echo "  Watch: gh run watch && curl -sf https://staging.glintstone.org/healthz"
