# example-agent/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY example-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY adk-shared ./adk-shared
# Create symlink for Python import (hyphens not allowed in module names)
RUN ln -sf adk-shared adk_shared

# Copy application code
COPY example-agent/ .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

EXPOSE $PORT

CMD ["python", "src/main.py"]
