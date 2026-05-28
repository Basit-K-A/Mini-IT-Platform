# AWS EC2 setup (Ubuntu)

One-time preparation for hosting Nexventory with Docker Compose.

## 1. Launch EC2

- **AMI:** Ubuntu Server 22.04 or 24.04 LTS
- **Instance type:** `t3.small` (or `t3.micro` for light demos)
- **Storage:** 20 GB gp3 minimum
- **Security group inbound:**
  - SSH `22` — your IP (or VPN)
  - HTTP `80` — `0.0.0.0/0` (or restrict to your IP)
  - HTTPS `443` — when you add TLS later

## 2. Connect

```powershell
ssh -i your-key.pem ubuntu@EC2_PUBLIC_IP
```

## 3. Install Docker

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Log out and back in so `docker` works without `sudo`:

```bash
exit
ssh -i your-key.pem ubuntu@EC2_PUBLIC_IP
docker run hello-world
```

## 4. Clone the repository

```bash
cd ~
git clone https://github.com/YOUR_USER/Mini-IT-Platform.git
cd Mini-IT-Platform
```

For CI `git pull`, configure a deploy key (see [CICD.md](CICD.md)).

## 5. Production environment file

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

Set at minimum:

- `POSTGRES_PASSWORD` — strong password
- `SECRET_KEY` — `openssl rand -hex 32`
- `CORS_ORIGINS` — your frontend origin(s)

## 6. First start

```bash
chmod +x scripts/deploy.sh
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose ps
curl http://localhost/health/ready
```

Open in browser: `http://EC2_PUBLIC_IP/docs`

## 7. Optional: firewall on the instance

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw enable
```

## 8. Connect GitHub Actions

Complete secrets in GitHub and add the Actions public key to `~/.ssh/authorized_keys` — [CICD.md](CICD.md).

After that, every push to `main` runs deploy automatically.

## Next steps

- Point a domain A record to the EC2 IP
- Add HTTPS with Let's Encrypt on nginx — [NGINX.md](NGINX.md)
- Deploy React dashboard to S3 + CloudFront (separate from this stack)
- Monitoring — [MONITORING.md](MONITORING.md)
