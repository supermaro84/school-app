#!/bin/bash
# Create the test users and groups from the CSV files in this folder.
# Run from the school_app directory: ./imports/load_imports.sh

set -e

echo "Applying migrations..."
uv run python manage.py migrate

# The user import looks roles up by name, so they must exist first
uv run python manage.py loaddata fixtures/userroles
uv run python manage.py import_event_options imports/event_options.csv

uv run python manage.py import_users imports/users.csv --output imports/credentials.csv
uv run python manage.py import_groups imports/groups.csv
uv run python manage.py import_announcements imports/announcements.csv
uv run python manage.py import_events imports/events.csv
uv run python manage.py import_events imports/timetable.csv

echo "Done! Temporary passwords are in imports/credentials.csv"
