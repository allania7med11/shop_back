#!/bin/sh

# Check if running as root and switch to appuser if needed
if [ "$(id -u)" = "0" ]; then
    # Fix permissions for vector_indexes directory if needed
    if [ -d "/vector_indexes" ]; then
        echo "Fixing permissions for /vector_indexes directory..."
        chown -R appuser:appuser /vector_indexes
        chmod 755 /vector_indexes
    fi

    # Switch to appuser and re-execute this script
    echo "Switching to appuser"
    exec su appuser -c "$0"
fi

echo "ENVIRONMENT=$ENVIRONMENT"
echo "MIGRATE=$MIGRATE"
echo "COLLECTSTATIC=$COLLECTSTATIC"
echo "RUN_SCRIPTS=$RUN_SCRIPTS"
echo "PORT=$PORT"

# Proceed with migrations if enabled
if [ "$MIGRATE" = "True" ]; then
    python manage.py migrate
fi

# Collect static files if enabled
if [ "$COLLECTSTATIC" = "True" ]; then
    # Don't change this message; we use it to detect when static files are generated successfully
    python manage.py collectstatic --noinput && echo "Generation completed successfully"
fi

# Execute additional scripts if enabled
if [ "$RUN_SCRIPTS" = "True" ]; then
    python manage.py runscripts
fi

# Start the application based on the environment
if [ "$ENVIRONMENT" = "debug" ]; then
    sleep infinity
elif [ "$ENVIRONMENT" = "dev" ]; then
    python manage.py runserver 0.0.0.0:$PORT
elif [ "$ENVIRONMENT" = "prod" ]; then
    daphne -b 0.0.0.0 -p $PORT shop_back.asgi:application
elif [ "$ENVIRONMENT" = "test" ]; then
    pytest
elif [ "$ENVIRONMENT" = "celery" ]; then
    celery -A shop_back worker -l INFO
fi
