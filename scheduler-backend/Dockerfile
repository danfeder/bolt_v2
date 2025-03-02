# Multi-stage build for a more optimized Docker image
# Stage 1: Builder - used for installing dependencies
FROM python:3.11-slim AS builder

# Set work directory for the build
WORKDIR /build

# Install build dependencies and avoid caching apt packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Final - minimal runtime image
FROM python:3.11-slim

# Add non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3001 \
    ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /build/wheels /wheels

# Install dependencies from wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copy application code
COPY app/ app/
COPY tests/ tests/
COPY data/ data/
COPY pytest.ini .

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Healthcheck to verify app is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Command to run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
