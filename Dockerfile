# Multi-stage Dockerfile for SSLTriage testing
# Supports both x64 and arm64 architectures

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    make \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install SSLyze
RUN pip install --no-cache-dir sslyze

# Install Jython for testing
RUN wget -q https://repo1.maven.org/maven2/org/python/jython-standalone/2.7.3/jython-standalone-2.7.3.jar -O /opt/jython-standalone.jar

# Copy project files
COPY SSLTriage.py /app/
COPY README.md /app/
COPY CHANGELOG.md /app/
COPY Makefile /app/
COPY .gitignore /app/

# Verify sslyze installation
RUN sslyze --version

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SSLYZE_PATH=/usr/local/bin/sslyze

# Create test target
FROM base AS test

# Run syntax validation
RUN python -m py_compile SSLTriage.py

# Run make test
RUN make test

# Final stage
FROM base AS final

# Add labels
LABEL maintainer="SSLTriage Team"
LABEL description="SSLTriage - Burp Suite SSL/TLS Scanner Extension"
LABEL version="1.0.0"

# Default command
CMD ["/bin/bash"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD sslyze --version || exit 1
