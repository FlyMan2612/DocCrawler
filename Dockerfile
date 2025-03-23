FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    tor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a non-root user
RUN useradd -m docscoop

# Create directories for Tor data
RUN mkdir -p /home/docscoop/.docscoop/tor_data && \
    chown -R docscoop:docscoop /home/docscoop/.docscoop

USER docscoop

# Set environment variables
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "docscoop_cli.py"] 