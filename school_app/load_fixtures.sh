#!/bin/bash

echo "Loading fixtures..."

# Reset database
rm db.sqlite3
uv run python manage.py migrate

# Load fixtures in dependency order
uv run python manage.py loaddata fixtures/users
uv run python manage.py loaddata fixtures/userprofiles
uv run python manage.py loaddata fixtures/groups
uv run python manage.py loaddata fixtures/groupprofiles
uv run python manage.py loaddata fixtures/announcements
uv run python manage.py loaddata fixtures/eventtypes
uv run python manage.py loaddata fixtures/eventstatuses
uv run python manage.py loaddata fixtures/events
uv run python manage.py loaddata fixtures/messagethreads
uv run python manage.py loaddata fixtures/messages

echo "Done! Login with: marek/marek"