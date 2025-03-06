#!/bin/bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate

poetry run python manage.py collectstatic --noinput
poetry run gunicorn -b 0.0.0.0:8000 --timeout 300 Dangnyang_Heroes.wsgi:application

