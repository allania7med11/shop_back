# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim 

ARG DEV_BUILD=False
ENV DEV_BUILD=$DEV_BUILD

# Install system packages and virtualenv
RUN apt-get update && apt-get install -y python3-venv libpq-dev gcc

# Install additional packages for development if DEV_BUILD is true
RUN if [ "$DEV_BUILD" = "true" ]; then \
        apt-get install -y curl git; \
    fi

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Create a virtual environment in the specified path
RUN python3 -m venv /opt/virtualenvs/production

# Activate the virtual environment by setting the PATH
ENV PATH="/opt/virtualenvs/production/bin:$PATH"

# Upgrade pip and install psycopg2 in the virtual environment
RUN pip install --upgrade pip && pip install psycopg2

# Install pip requirements in the virtual environment
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set the working directory and copy the project files
WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 1000 --disabled-password --gecos "" appuser && \
    chown -R appuser /app
USER appuser

# Expose the application port
EXPOSE 8000

# Set the entrypoint and command
ENTRYPOINT ["sh", "./run.sh"]
CMD ["dev", "8000"]
