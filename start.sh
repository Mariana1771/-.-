#!/bin/bash
cd backend
python manage.py migrate
gunicorn lingua.wsgi:application --bind 0.0.0.0:$PORT --workers 4
