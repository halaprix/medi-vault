# Self-Signed SSL Setup (Local Development)

This guide explains how to set up HTTPS for local development using a self-signed
certificate. This is optional but recommended for testing security features like
HSTS, secure cookies, and CSP headers.

## Quick Start

```bash
# 1. Generate a self-signed certificate (valid 365 days)
mkdir -p infra/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout infra/nginx/ssl/medi-vault.key \
    -out infra/nginx/ssl/medi-vault.crt \
    -subj "/CN=medi-vault.local"

# 2. Add to /etc/hosts (optional, for nicer URLs)
echo "127.0.0.1 medi-vault.local" | sudo tee -a /etc/hosts

# 3. Ensure docker-compose mounts the SSL volume
# The default docker-compose.yml already maps:
#   ./infra/nginx/ssl:/etc/nginx/ssl:ro

# 4. Rebuild and restart
docker compose up -d --build nginx

# 5. Visit https://medi-vault.local (accept the self-signed cert warning)
```

## Browser Warning

Self-signed certificates trigger browser security warnings. For Chrome/Chromium:

1. Click **Advanced** on the warning page
2. Click **Proceed to medi-vault.local (unsafe)**
3. The site loads normally — encryption works, just not third-party verified

For Firefox:
1. Click **Advanced…**
2. Click **Accept the Risk and Continue**

## Why Self-Signed?

- **Free** — no CA fees for local development
- **Encrypted** — traffic is still encrypted with TLS 1.2/1.3
- **Test security headers** — CSP, HSTS, and other headers only work over HTTPS
- **No domain needed** — works on localhost or any hostname

## Production

For production deployments, use a proper certificate authority:

- **Let's Encrypt** (free, automated): Use certbot with the nginx plugin
- **Cloudflare**: Origin certificates + Full (strict) SSL mode
- **AWS ACM**: If deploying behind an ALB/CloudFront

Replace the certificate paths in `infra/nginx/default.conf` with your production
certificate locations.

## Troubleshooting

**"ERR_SSL_PROTOCOL_ERROR"**: Ensure port 443 is exposed and Nginx is running.
Check `docker compose logs nginx` for errors.

**"Connection refused"**: Ensure the docker-compose service is up.
Run `docker compose ps` to verify.

**Certificate not found**: Verify the files exist at `infra/nginx/ssl/medi-vault.crt`
and `infra/nginx/ssl/medi-vault.key`. Re-run the openssl command if missing.
