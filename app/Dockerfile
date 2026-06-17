# ---------------------------------------------------------------------------
# EcoChain Exchange - Application Dockerfile
# Multi-stage build for a small, production-friendly image
# ---------------------------------------------------------------------------

FROM python:3.12-slim AS base

# Avoid .pyc files & enable unbuffered logging (good for container logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create non-root user for security
RUN useradd -m ecochain && chown -R ecochain:ecochain /app
USER ecochain

EXPOSE 5000

# Health check used by Docker / orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run with gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]
