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

`deploy/update.sh` brings the server to the latest commit of `main`: fetch,
install dependencies, migrate, collect static files, restart. It runs as the
`school` user, which needs permission to restart the app. Once:

```bash
echo 'school ALL=(root) NOPASSWD: /usr/bin/systemctl restart school-app' > /etc/sudoers.d/school-app
chmod 440 /etc/sudoers.d/school-app
visudo -c
```

Then update with:

```bash
sudo -u school -H /srv/school-app/deploy/update.sh
```

Any local edits to tracked files on the server are discarded; `.env`, the
database and uploads are not tracked and stay. To test another branch:

```bash
sudo -u school -H env DEPLOY_BRANCH=<branch> /srv/school-app/deploy/update.sh
```

The next auto-deploy switches the server back to `main`.

`update.sh` does not touch the server's config. When `deploy/nginx.conf` or
`deploy/school-app.service` change, copy them again as in step 6, then run
`systemctl daemon-reload && systemctl restart school-app` and
`nginx -t && systemctl reload nginx`.

## Auto-deploy

`.github/workflows/deploy.yml` runs the tests on every push to `main` and,
when they pass, connects to the Droplet over SSH, which runs `update.sh`.
It can also be started from **Actions → Test and deploy → Run workflow**.
Set up the sudoers rule from [Updating](#updating) first.

### 1. A deploy key that can only run the update

On your own computer, create a key pair used for nothing else (no passphrase):

```bash
ssh-keygen -t ed25519 -N '' -C github-deploy -f ~/.ssh/school-app-deploy
cat ~/.ssh/school-app-deploy.pub
```

On the Droplet, let that key log in as `school`, restricted to the update
script (`restrict` turns off the shell, port forwarding and the rest):

```bash
mkdir -p /home/school/.ssh
echo 'command="/srv/school-app/deploy/update.sh",restrict <paste the .pub line here>' >> /home/school/.ssh/authorized_keys
chown -R school:school /home/school/.ssh
chmod 700 /home/school/.ssh && chmod 600 /home/school/.ssh/authorized_keys
```

Check it from your computer; it should print the update steps and end with
`==> Deployed`:

```bash
ssh -i ~/.ssh/school-app-deploy school@203.0.113.10
```

### 2. GitHub secrets

The Droplet's SSH host key, so GitHub Actions only talks to your server:

```bash
ssh-keyscan -t ed25519 203.0.113.10
```

To be sure the output is really your Droplet, compare the fingerprint from
`ssh-keyscan -t ed25519 203.0.113.10 | ssh-keygen -lf -` with
`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` run on the Droplet.

In GitHub: **Settings → Secrets and variables → Actions → New repository
secret**, add:

| Secret | Value |
|---|---|
| `DROPLET_HOST` | the Droplet's IP, e.g. `203.0.113.10` |
| `DROPLET_SSH_KEY` | the whole private key: `cat ~/.ssh/school-app-deploy` |
| `DROPLET_KNOWN_HOSTS` | the `ssh-keyscan` line from above |

Then delete the private key from your computer if you don't want a copy
outside GitHub.

### 3. Watching deploys

Every push to `main` shows up under **Actions**. If the tests fail, nothing is
deployed. The deploy job's log shows the output of `update.sh`; a failure in
any step stops the update and marks the run as failed. Server-side logs are
under [Troubleshooting](#troubleshooting).

Each deploy restarts the app, so it is unavailable for a second or two.

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
