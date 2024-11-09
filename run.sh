#!/bin/sh
echo "ENVIRONMENT=$ENVIRONMENT"
echo "MIGRATE=$MIGRATE"
echo "COLLECTSTATIC=$COLLECTSTATIC"
echo "PORT=$PORT"


# Proceed with migrations if enabled
if [ "$MIGRATE" = "True" ]; then
    python manage.py migrate
fi

# Collect static files if enabled
if [ "$COLLECTSTATIC" = "True" ]; then
    python manage.py collectstatic --noinput && echo "Static files generated successfully"
fi

# Start the application based on the environment
if [ "$ENVIRONMENT" = "debug" ]; then
    sleep infinity
elif [ "$ENVIRONMENT" = "dev" ]; then
    python manage.py runserver 0.0.0.0:$PORT
elif [ "$ENVIRONMENT" = "prod" ]; then
    gunicorn shop_back.wsgi:application --bind 0.0.0.0:$PORT
elif [ "$ENVIRONMENT" = "test" ]; then
    pytest
fi
