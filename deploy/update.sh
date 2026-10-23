#!/usr/bin/env bash
# Updates the running app to the latest commit of DEPLOY_BRANCH (default: main).
# Runs as the `school` user: by hand with
#   sudo -u school /srv/school-app/deploy/update.sh
# or from GitHub Actions through the restricted deploy key (see README.md).
#
# Everything runs inside main(), so bash has read the whole script before the
# checkout below replaces this file with its new version.

main() {
    set -euo pipefail

    local app_dir=/srv/school-app
    local branch="${DEPLOY_BRANCH:-main}"
    export PATH="/usr/local/bin:$PATH"

    # One deploy at a time; a second one waits for the first to finish.
    exec 9>"$HOME/.school-app-deploy.lock"
    flock 9

    cd "$app_dir"
    echo "==> Fetching $branch"
    git fetch --quiet origin "$branch"
    # Discards local edits to tracked files; .env, the database and uploads
    # are ignored by git and stay untouched.
    git checkout --quiet --force -B "$branch" "origin/$branch"
    git log -1 --format='    %h %s'

    echo "==> Installing dependencies"
    uv sync --frozen --no-dev --quiet

    cd "$app_dir/school_app"
    echo "==> Migrating database"
    ../.venv/bin/python manage.py migrate --noinput
    echo "==> Collecting static files"
    ../.venv/bin/python manage.py collectstatic --noinput --verbosity 0

    echo "==> Restarting app"
    # Allowed without a password by /etc/sudoers.d/school-app.
    sudo -n /usr/bin/systemctl restart school-app
    echo "==> Deployed"
}

main "$@"; exit $?
