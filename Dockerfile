# Multi-Agent Jira Card Creation System Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    wget https://download.oracle.com/otn_software/linux/instantclient/1916000/instantclient-basic-linux.x64-19.16.0.0.0dbru.zip && \
    unzip instantclient-basic-linux.x64-19.16.0.0.0dbru.zip && \
    rm instantclient-basic-linux.x64-19.16.0.0.0dbru.zip && \
    sh -c "echo /opt/oracle/instantclient_19_16 > /etc/ld.so.conf.d/oracle-instantclient.conf" && \
    ldconfig

# Set Oracle environment variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_19_16:$LD_LIBRARY_PATH
ENV TNS_ADMIN=/opt/oracle/instantclient_19_16
ENV ORACLE_HOME=/opt/oracle/instantclient_19_16

# Install Node.js for Angular frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY *.md ./
COPY *.py ./

# Build Angular frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# Back to app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p logs repositories .repo_cache .context_cache

# Set environment variables
ENV PYTHONPATH=/app
ENV REPOSITORY_BASE_PATH=/app/repositories

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]