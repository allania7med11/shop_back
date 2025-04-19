# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim 

ARG DEV_BUILD=False
ENV DEV_BUILD=$DEV_BUILD

# Define the user ID as a build argument with a default value
ARG APP_UID=1000
ENV APP_UID=$APP_UID

# Install system packages and set up locales
RUN apt-get update && apt-get install -y \
    locales \
    libpq-dev \
    gcc \
    python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Generate the locale for en_US.UTF-8
RUN sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

# Set environment variables for the locale
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Create a non-root user with the specified UID and adds permission to access the /app folder
RUN adduser -u $APP_UID --disabled-password --gecos "" appuser

# Install additional packages for development if DEV_BUILD is true
RUN if [ "$DEV_BUILD" = "true" ]; then \
        apt-get update && apt-get install -y curl git sudo && \
        echo "appuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers; \
    fi

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Create vector_indexes directory and set permissions
RUN mkdir -p /vector_indexes/products && \
    chown -R appuser:appuser /vector_indexes && \
    chmod 755 /vector_indexes

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

# Change ownership of the virtual environment and /app directory to the non-root user
RUN chown -R appuser:appuser /opt/virtualenvs/production /app


# Expose the application port
EXPOSE 8000

# Set the entrypoint and command
ENTRYPOINT ["sh", "./run.sh"]
CMD ["dev", "8000"]
