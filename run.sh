#!/bin/sh
echo "envs $ENVIRONMENT $PORT"
python manage.py makemigrations
python manage.py migrate 
if [ "$COLLECTSTATIC" = "True" ]; then
    python manage.py collectstatic --noinput && echo "Generation completed successfully"
fi
if [ "$ENVIRONMENT" = "debug" ]; then
    sleep infinity
elif [ "$ENVIRONMENT" = "dev" ]; then
    python manage.py runserver 0.0.0.0:$PORT
elif [ "$ENVIRONMENT" = "prod" ]; then
    gunicorn shop_back.wsgi:application --bind 0.0.0.0:$PORT
fi
