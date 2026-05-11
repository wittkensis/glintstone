# Glintstone v2 — Deploy

Two deploy paths, same end state: a versioned release directory on the
Hostinger VPS with a `current` symlink that gets swapped atomically.

```
/var/www/glintstone/
  ├── current                  → releases/20260511-103200-abc1234
  ├── shared/
  │   └── .env                 (per-environment secrets, never in git)
  └── releases/
      ├── 20260511-103200-abc1234/   (latest)
      ├── 20260511-101500-9def567/
      └── 20260510-180000-1234567/   (older — auto-trimmed beyond KEEP_RELEASES)
```

## Automated deployment (preferred)

Pushing to GitHub triggers deploys. Configure secrets once; nothing else
needed.

### Required GitHub repository secrets

| Secret | Status | Value |
|---|---|---|
| `HOSTINGER_HOST` | ✅ set | 76.13.208.149 |
| `HOSTINGER_SSH_KEY` | ✅ set | `~/.ssh/glintstone_deploy` (private key) |
| `DATABASE_URL_PROD` | ✅ set | Neon production branch URL |
| `DATABASE_URL_STAGING` | ⚠️ pending | Create a Neon staging branch, then: `gh secret set DATABASE_URL_STAGING --body "postgresql://..."` |

To create the Neon staging branch:
1. Neon Console → Project → Branches → New Branch → name it `staging`
2. Copy the connection string
3. `gh secret set DATABASE_URL_STAGING --body "postgresql://..." --repo wittkensis/glintstone`

### GitHub Environments

Both environments are created. To add a required-reviewer gate to production
(prevents auto-deploy on `main` without a click-through approval):

```
Settings → Environments → production → Required reviewers → add yourself
```

- `production` — currently unprotected; add reviewer gate above
- `staging` — no reviewer; auto-deploys from `staging` branch

### Trigger rules

| Action | Result |
|---|---|
| Push to `staging` branch | tests run → deploy to staging |
| Push to `main` | tests run → deploy to production (with approval gate) |
| `workflow_dispatch` | manual deploy from the Actions tab |

### One-time VPS setup

If this is a fresh VPS, run `provision.sh` once (see "Hostinger VPS Setup"
below) and place a per-environment `.env` in `/var/www/glintstone/shared/.env`.
The deploy script never writes this file — only the symlink to it.

## Manual deployment (local machine)

```bash
./ops/deploy/deploy.sh                  # deploy all targets
./ops/deploy/deploy.sh api              # API only
./ops/deploy/deploy.sh app marketing    # web app + marketing
```

Requires `DEPLOY_HOST` either in your `.env` or as an env var.

## Rollback

```bash
./ops/deploy/rollback.sh                  # list releases on the server
./ops/deploy/rollback.sh 20260511-101500-9def567   # roll back to that release
```

Rollback is one symlink change — same atomicity as a forward deploy.

## Migrations

`data-model/migrate.py` runs against whatever `DATABASE_URL` is in the
active environment. GitHub Actions runs `migrate.py up` against the
target Neon branch BEFORE swapping the symlink — so a failed migration
fails the deploy without affecting the running release.

## Hostinger VPS Setup (one-time)

### SSH key

```bash
ssh-keygen -t ed25519 -C "glintstone-deploy" -f ~/.ssh/glintstone_deploy
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

### Hostinger VPS (hPanel)

1. KVM 2 (8 GB / 100 GB / 2 CPU), Alpine Linux
2. Paste the public key during setup (or hPanel → VPS → Manage → Settings → SSH Keys)
3. Firewall: open TCP 22, 80, 443 (hPanel → VPS → Manage → Security)

### Provision

```bash
ssh root@YOUR_VPS_IP 'sh -s' < ops/deploy/provision.sh
```

Installs: nginx, Python 3, supervisor, certbot. **Postgres is no longer
installed on the VPS** — the database lives at Neon.

### Per-environment .env

Create `/var/www/glintstone/shared/.env` on the VPS:

```bash
ssh deploy@YOUR_VPS_IP "mkdir -p /var/www/glintstone/shared && cat > /var/www/glintstone/shared/.env" << 'EOF'
APP_ENV=production
APP_DEBUG=false
DATABASE_URL=postgresql://USER:PASS@HOST/dbname?sslmode=require
API_PORT=8001
WEB_PORT=8002
API_URL=https://api.glintstone.org
WEB_URL=https://app.glintstone.org
MARKETING_URL=https://glintstone.org
IMAGE_PATH=/var/www/glintstone/shared/images
EOF
```

### DNS

| Record | Name | Value |
|---|---|---|
| A | @ | VPS_IP |
| A | api | VPS_IP |
| A | app | VPS_IP |
| A | staging | VPS_IP |
| A | www | VPS_IP |

### SSL

```bash
ssh root@VPS_IP "certbot --nginx -d glintstone.org -d www.glintstone.org -d api.glintstone.org -d app.glintstone.org -d staging.glintstone.org"
```

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `DEPLOY_HOST not set` from CI | Missing `HOSTINGER_HOST` repo secret |
| `Permission denied (publickey)` | `HOSTINGER_SSH_KEY` secret doesn't match the public key on the VPS |
| `502 Bad Gateway` after deploy | supervisor didn't restart — check `ssh deploy@host "sudo supervisorctl status"` |
| Migrations failed in CI | Bad `DATABASE_URL_*` secret, or a SQL error in the new migration |
| CORS errors after deploy | `API_URL` / `WEB_URL` in `shared/.env` use `http://` instead of `https://` |
| Rollback fails | The release directory was trimmed — increase `KEEP_RELEASES` |
