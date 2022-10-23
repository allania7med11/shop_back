#!/bin/sh

python manage.py migrate --noinput

mkdir static

python manage.py collectstatic --noinput

gunicorn shop_back.wsgi:application --bind 0.0.0.0:8000