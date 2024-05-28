# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim 

ARG DEV_BUILD=False

ENV DEV_BUILD=$DEV_BUILD

RUN if [ "$DEV_BUILD" = "true" ]; then \
        apt-get update && apt-get install -y curl git; \
    fi
EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 1000 --disabled-password --gecos "" appuser
RUN chown -R appuser /app
USER appuser

ENTRYPOINT ["sh", "./run.sh"]
CMD ["dev", "8000"]
