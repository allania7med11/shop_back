#!/bin/sh

python manage.py migrate --noinput

gunicorn shop_back.wsgi:application --bind 0.0.0.0:8000