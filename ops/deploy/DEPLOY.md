# Glintstone v2 — Deploy Protocol

Target: Hostinger VPS (Alpine Linux, 8GB RAM, 100GB storage, 2 CPU)

---

## 1. SSH Key Setup (one-time, local machine)

```bash
# Generate key (if you don't have one)
ssh-keygen -t ed25519 -C "glintstone-deploy" -f ~/.ssh/glintstone_deploy

# Add to SSH agent
ssh-add ~/.ssh/glintstone_deploy

# Copy public key to clipboard
pbcopy < ~/.ssh/glintstone_deploy.pub
```

Add to `~/.ssh/config`:

```
Host glintstone
    HostName YOUR_VPS_IP
    User deploy
    IdentityFile ~/.ssh/glintstone_deploy
    Port 22
```

---

## 2. Hostinger VPS Setup (one-time, hPanel)

1. **Create VPS** — Choose KVM 2 plan (8GB/100GB/2CPU)
2. **OS** — Select Alpine Linux (plain, no control panel)
3. **SSH key** — Paste `~/.ssh/glintstone_deploy.pub` during setup
   - Or add later: hPanel > VPS > Manage > Settings > SSH Keys
4. **Note the IP** — Update `~/.ssh/config` and `.env` with it

### hPanel Firewall

hPanel > VPS > Manage > Security > Firewall

Create a firewall group with these rules:

| Protocol | Port | Source | Action |
|----------|------|--------|--------|
| TCP      | 22   | Any    | Accept |
| TCP      | 80   | Any    | Accept |
| TCP      | 443  | Any    | Accept |

Apply the group to your server. Without these rules, all inbound traffic is dropped.

---

## 3. First-Time Server Provisioning

```bash
# SSH in as root (password from Hostinger email)
ssh root@76.13.208.149

# Or pipe the provision script directly
ssh root@76.13.208.149 'sh -s' < ops/deploy/provision.sh
```

The provision script installs: nginx, Python 3, PostgreSQL 17, supervisor, certbot.

**Save the DB password it outputs.** You need it for the .env file.

### Post-provision checklist

```bash
# 1. Create production .env on the server
ssh deploy@76.13.208.149 "cat > /var/www/glintstone/.env" << 'EOF'
APP_ENV=production
APP_DEBUG=false

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=glintstone
DB_USER=glintstone
DB_PASSWORD=THE_PASSWORD_FROM_PROVISION

API_PORT=8001
WEB_PORT=8002

API_URL=https://api.glintstone.org
WEB_URL=https://app.glintstone.org
MARKETING_URL=https://glintstone.org

IMAGE_PATH=/var/www/glintstone/data/images
EOF
```

---

## 4. DNS (one-time, your domain registrar)

Add A records pointing to VPS IP:

| Record | Name | Value |
|--------|------|-------|
| A      | @    | VPS_IP |
| A      | api  | VPS_IP |
| A      | app  | VPS_IP |
| A      | www  | VPS_IP |

Wait for propagation (~5 min to 24 hours).

---

## 5. SSL Certificates (one-time, on server)

```bash
ssh root@YOUR_VPS_IP
certbot --nginx \
    -d glintstone.org \
    -d www.glintstone.org \
    -d api.glintstone.org \
    -d app.glintstone.org
```

Certbot auto-renews via cron.

---

## 6. Deploy

Set `DEPLOY_HOST` in your local `.env`:

```
DEPLOY_HOST=YOUR_VPS_IP
```

### Deploy everything

```bash
./ops/deploy/deploy.sh
```

### Deploy specific targets

```bash
./ops/deploy/deploy.sh api              # API only
./ops/deploy/deploy.sh app              # Web app only
./ops/deploy/deploy.sh marketing        # Marketing site only
./ops/deploy/deploy.sh api app          # API + web app
```

### What each target does

| Target | Syncs | Restarts |
|--------|-------|----------|
| `api` | `core/`, `api/`, `data-model/`, `requirements.txt` | glintstone-api (supervisor) |
| `app` | `core/`, `app/`, `data-model/`, `requirements.txt` | glintstone-web (supervisor) |
| `marketing` | `marketing/` | nginx reload |

Both `api` and `app` also run `pip install` and `data-model/migrate.py`.

---

## 7. Server Commands Reference

```bash
# SSH in
ssh glintstone                          # uses ~/.ssh/config alias

# Logs
ssh glintstone "tail -50 /var/log/glintstone-api.err.log"
ssh glintstone "tail -50 /var/log/glintstone-web.err.log"

# Restart services
ssh glintstone "sudo supervisorctl restart glintstone-api"
ssh glintstone "sudo supervisorctl restart glintstone-web"
ssh glintstone "sudo rc-service nginx reload"

# Service status
ssh glintstone "sudo supervisorctl status"

# DB access
ssh glintstone "psql -U glintstone glintstone"
```

---

## Troubleshooting

**Can't SSH in** — Check hPanel firewall has port 22 open. Hostinger's managed firewall is separate from the OS firewall.

**502 Bad Gateway** — uvicorn not running. Check `supervisorctl status` and error logs.

**CORS errors** — Verify `API_URL` and `WEB_URL` in production `.env` use `https://`.

**certbot fails** — DNS not propagated yet. Verify with `dig api.glintstone.org`.
