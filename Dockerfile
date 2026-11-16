# CloudPulse Containerfile
FROM python:3.11-slim

WORKDIR /app

# Install system utilities for monitoring
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iproute2 \
    dnsutils \
    procps \
    systemd \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all application code
COPY . .

# Set environment
ENV PYTHONPATH=/app \
    FLASK_APP=backend.app.main:app \
    PORT=5000 \
    HOST=0.0.0.0

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "backend.app.main:app"]
