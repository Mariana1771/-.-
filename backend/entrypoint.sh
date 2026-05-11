#!/usr/bin/env sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn lingua.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60

