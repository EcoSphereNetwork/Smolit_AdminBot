# Stage 1: Build environment
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Stage 2: Runtime environment
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    apparmor \
    apparmor-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -r -s /bin/bash rootbot

# Copy application files
COPY . .

# Set correct permissions
RUN chown -R rootbot:rootbot /app && \
    chmod -R 750 /app && \
    chmod 600 rootbot.conf

# Copy AppArmor profile
COPY rootbot.apparmor /etc/apparmor.d/rootbot
RUN apparmor_parser -r /etc/apparmor.d/rootbot

# Create necessary directories with correct permissions
RUN mkdir -p /var/log/rootbot /var/run/rootbot /var/lib/rootbot && \
    chown -R rootbot:rootbot /var/log/rootbot /var/run/rootbot /var/lib/rootbot && \
    chmod 750 /var/log/rootbot /var/run/rootbot /var/lib/rootbot

# Switch to non-root user
USER rootbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/health')"

# Expose necessary ports
EXPOSE 5000

# Set entrypoint and default command
ENTRYPOINT ["python3"]
CMD ["-m", "root_bot"]

