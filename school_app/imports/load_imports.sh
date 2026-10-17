#!/bin/bash
# Create the test data from the CSV files of one language folder.
# Run from the school_app directory: ./imports/load_imports.sh [en|pl]  (default: en)

set -e

LANG_DIR="imports/${1:-en}"
if [ ! -d "$LANG_DIR" ]; then
    echo "No data folder $LANG_DIR. Available: $(ls -d imports/*/ | xargs -n1 basename | tr '\n' ' ')"
    exit 1
fi

echo "Loading test data from $LANG_DIR..."
uv run python manage.py migrate

# Lookups first: users need roles, events need types and statuses
uv run python manage.py import_roles "$LANG_DIR/roles.csv"
uv run python manage.py import_event_options "$LANG_DIR/event_options.csv"

uv run python manage.py import_users "$LANG_DIR/users.csv" --output "$LANG_DIR/credentials.csv"
uv run python manage.py import_groups "$LANG_DIR/groups.csv"
uv run python manage.py import_announcements "$LANG_DIR/announcements.csv"
uv run python manage.py import_events "$LANG_DIR/events.csv"
uv run python manage.py import_events "$LANG_DIR/timetable.csv"

echo "Done! Temporary passwords are in $LANG_DIR/credentials.csv"
