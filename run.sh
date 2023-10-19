#!/bin/sh
echo "envs $ENVIRONMENT $PORT"
python manage.py makemigrations
python manage.py migrate 
if [ "$ENVIRONMENT" = "debug" ]; then
    sleep infinity
elif [ "$ENVIRONMENT" = "dev" ]; then
    python manage.py collectstatic --noinput
    python manage.py runserver $PORT
elif [ "$ENVIRONMENT" = "prod" ]; then
    gunicorn shop_back.wsgi:application --bind 0.0.0.0:$PORT
fi
