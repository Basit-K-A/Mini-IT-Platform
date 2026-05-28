# CI/CD — GitHub Actions → AWS EC2

Automated pipeline: push to `main` → build Docker images on GitHub → SSH to EC2 → `git pull` → `docker compose up -d --build`.

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | Push / PR to `main` | Validate Compose, build API, smoke test |
| [.github/workflows/deploy.yml](../.github/workflows/deploy.yml) | Push to `main` | Build, then deploy to EC2 via SSH |

## Flow

```
Developer: git push origin main
        │
        ▼
GitHub Actions (ubuntu-latest)
  ├─ job: build — docker compose config + build
  └─ job: deploy — SSH → EC2 → scripts/deploy.sh
        │
        ▼
EC2 Ubuntu
  ├─ git pull origin main
  └─ docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## GitHub Secrets (required)

In the repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Example | Description |
|--------|---------|-------------|
| `EC2_HOST` | `3.15.123.45` or `api.example.com` | Public IP or DNS of your EC2 instance |
| `EC2_USER` | `ubuntu` | SSH user (Ubuntu AMI default is `ubuntu`) |
| `EC2_SSH_KEY` | *(full private key)* | Private key matching the public key on the server |
| `EC2_DEPLOY_PATH` | `/home/ubuntu/Mini-IT-Platform` | Absolute path to the cloned repo on EC2 |

Optional:

| Secret | Default | Description |
|--------|---------|-------------|
| `EC2_SSH_PORT` | `22` | SSH port if not 22 |

**Never commit** private keys or `.env.prod` to GitHub.

## Generate SSH keys (Windows / Linux)

On your **local machine**:

```powershell
ssh-keygen -t ed25519 -C "github-actions-nexventory" -f "$env:USERPROFILE\.ssh\nexventory_deploy"
```

This creates:

- `nexventory_deploy` — **private** → paste into GitHub secret `EC2_SSH_KEY`
- `nexventory_deploy.pub` — **public** → add to EC2

## Configure EC2 for GitHub Actions

1. SSH into the server as `ubuntu`:
   ```bash
   ssh -i your-key.pem ubuntu@EC2_HOST
   ```

2. Add the **public** key to `authorized_keys`:
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   nano ~/.ssh/authorized_keys
   # Paste contents of nexventory_deploy.pub on its own line
   chmod 600 ~/.ssh/authorized_keys
   ```

3. Test from your PC:
   ```powershell
   ssh -i $env:USERPROFILE\.ssh\nexventory_deploy ubuntu@EC2_HOST
   ```

4. Ensure security group allows **SSH (22)** from GitHub Actions IPs, or temporarily from your IP for testing.  
   For production, consider [GitHub's published IP ranges](https://api.github.com/meta) or a self-hosted runner on the same VPC.

## Server-side setup (one time)

See [EC2_SETUP.md](EC2_SETUP.md) for Docker, clone repo, and `.env.prod`.

After clone:

```bash
cd /home/ubuntu/Mini-IT-Platform
cp .env.prod.example .env.prod
nano .env.prod   # set SECRET_KEY, POSTGRES_PASSWORD, CORS_ORIGINS
chmod +x scripts/deploy.sh
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

`git pull` on the server requires either:

- **HTTPS** with a deploy token stored on the server, or
- **SSH deploy key** added to GitHub (read-only) in `~/.ssh` on EC2

Example deploy key on EC2:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub
# Add as Deploy Key in GitHub repo settings (read access)
```

Configure git remote:

```bash
git remote set-url origin git@github.com:YOUR_USER/Mini-IT-Platform.git
```

## Manual deploy (without Actions)

On EC2:

```bash
cd /home/ubuntu/Mini-IT-Platform
./scripts/deploy.sh
```

## Troubleshooting CI/CD

| Issue | Fix |
|-------|-----|
| `Permission denied (publickey)` | Check `EC2_SSH_KEY` secret (full PEM/OpenSSH private key, including headers) |
| `git pull` fails on EC2 | Configure deploy key or credentials on the server |
| Deploy succeeds but 502 | Run `docker compose logs api` on EC2; check `.env.prod` passwords |
| Build fails on GitHub | Open Actions tab → failed job → logs |
| Port 80 not reachable | EC2 security group: allow HTTP (80) from `0.0.0.0/0` or your IP |

## Security practices

- Use **repository secrets** only for SSH and host info — not app secrets (those stay in `.env.prod` on EC2).
- Restrict SSH to known IPs when possible.
- Rotate `SECRET_KEY` and DB passwords independently of GitHub.
- Use separate SSH keys for humans vs CI.
