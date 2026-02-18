FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src /app/src
COPY dagster.yaml /app/dagster.yaml
COPY workspace.yaml /app/workspace.yaml

# Set python path
ENV PYTHONPATH=/app

# Default command (will be overridden in docker-compose)
CMD ["python"]
