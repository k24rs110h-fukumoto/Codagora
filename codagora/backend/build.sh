#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

echo "Installing dependencies..."

python -m pip install \
    --upgrade pip

python -m pip install \
    -r requirements.txt


echo "Running database migrations..."

DJANGO_SETTINGS_MODULE=config.settings.render \
python manage.py migrate \
    --noinput


echo "Collecting static files..."

DJANGO_SETTINGS_MODULE=config.settings.render \
python manage.py collectstatic \
    --noinput


echo "Running Django system check..."

DJANGO_SETTINGS_MODULE=config.settings.render \
python manage.py check


echo "Build completed."