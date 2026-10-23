# Test deployment on a DigitalOcean Droplet

One small Droplet running everything: nginx in front, gunicorn running Django,
SQLite as the database and uploads stored on the Droplet's disk. Plain HTTP on
the Droplet's IP address (no domain yet).

Layout on the server:

| Path | What |
|---|---|
| `/srv/school-app` | the git checkout, owned by the `school` user |
| `/srv/school-app/school_app/.env` | settings and secrets |
| `/srv/school-app/school_app/db.sqlite3` | the database |
| `/srv/school-app/school_app/uploads/` | uploaded images and documents |
| `/srv/school-app/school_app/staticfiles/` | output of `collectstatic` |

Commands below use `203.0.113.10` as the Droplet's IP; use your own.

## 1. Create the Droplet

In the DigitalOcean console: **Create → Droplets**, Ubuntu 24.04 LTS,
Basic / Regular, the **$6/mo** size (1 GB RAM), a region near your users
(e.g. Frankfurt), and add your SSH key. Then:

```bash
ssh root@203.0.113.10
```

## 2. Prepare the server

```bash
apt update && apt upgrade -y
apt install -y nginx git

# 1 GB swap so builds and migrations don't run out of memory
fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Firewall: SSH and HTTP only
ufw allow OpenSSH && ufw allow 'Nginx HTTP' && ufw --force enable

# uv (installs Python 3.14 for the project by itself)
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# Dedicated user that runs the app
adduser --system --group --home /home/school --shell /bin/bash school
```

## 3. Get the code

```bash
mkdir -p /srv/school-app && chown school:school /srv/school-app
sudo -u school -H git clone https://github.com/supermaro84/school-app.git /srv/school-app
cd /srv/school-app
sudo -u school -H git checkout main      # or the branch you want to test
sudo -u school -H uv sync --frozen --no-dev
```

Cloning over HTTPS works if the repository is public; if it is private, add a
[deploy key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
for the `school` user and clone over SSH instead.

## 4. Configure

```bash
cd /srv/school-app/school_app
sudo -u school cp .env.example .env
sudo -u school chmod 600 .env
# Generate a secret key to paste into .env
/srv/school-app/.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(50))"
sudo -u school nano .env
```

Set at least:

```ini
DEBUG=False
DJANGO_SECRET_KEY=<the generated key>
ALLOWED_HOSTS=203.0.113.10
```

Leave `ACCESS_KEY`, `SECRET_KEY` and `BUCKET_NAME` empty so uploads stay on
the Droplet's disk. Theme settings work as described in `.env.example`.

## 5. Database and static files

```bash
cd /srv/school-app/school_app
sudo -u school -H ../.venv/bin/python manage.py migrate
sudo -u school -H ../.venv/bin/python manage.py collectstatic --noinput
```

Then either create an admin account:

```bash
sudo -u school -H ../.venv/bin/python manage.py createsuperuser
```

or load the demo data with `sudo -u school -H bash load_fixtures.sh`
(it deletes the database first). The demo users have weak passwords such as
`marek/marek`, and the site is public, so change them right after loading.

## 6. Start the app and nginx

```bash
cp /srv/school-app/deploy/school-app.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now school-app

cp /srv/school-app/deploy/nginx.conf /etc/nginx/sites-available/school-app
ln -s /etc/nginx/sites-available/school-app /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

Open `http://203.0.113.10/`.

Plain HTTP means passwords travel unencrypted: use test accounts only.

## Updating

```bash
cd /srv/school-app
sudo -u school -H git pull
sudo -u school -H uv sync --frozen --no-dev
cd school_app
sudo -u school -H ../.venv/bin/python manage.py migrate
sudo -u school -H ../.venv/bin/python manage.py collectstatic --noinput
systemctl restart school-app
```

## Backups

Everything worth keeping is the database, the uploads and `.env`:

```bash
cd /srv/school-app/school_app
sqlite3 db.sqlite3 ".backup /root/db-$(date +%F).sqlite3"   # apt install sqlite3
tar czf /root/uploads-$(date +%F).tar.gz uploads .env
```

Copy them off the server with `scp root@203.0.113.10:/root/db-*.sqlite3 .`.
DigitalOcean's Droplet backups (+20% of the Droplet price) also cover them.

## Troubleshooting

```bash
systemctl status school-app        # is gunicorn running?
journalctl -u school-app -n 100    # Django/gunicorn errors and requests
tail -n 50 /var/log/nginx/error.log
```

- **400 Bad Request:** the address you opened isn't in `ALLOWED_HOSTS`.
- **502 Bad Gateway:** gunicorn isn't running; check `journalctl -u school-app`.
- **Page without styling:** run `collectstatic` again.
- **Changed `.env`:** run `systemctl restart school-app`.

## Adding a domain later

Point the domain's A record at the Droplet's IP (or use
`203-0-113-10.sslip.io`), set `server_name` in the nginx config, add the
hostname to `ALLOWED_HOSTS`, then `apt install certbot python3-certbot-nginx`,
`certbot --nginx -d <hostname>` and `ufw allow 'Nginx Full'`.
