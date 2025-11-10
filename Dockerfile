# Minimal Dockerfile for Alma note-taking app
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies using UV
RUN uv sync --frozen --no-dev

# Copy application code
COPY alma ./alma

# Create directories for data persistence
RUN mkdir -p /app/notes /app/.indexes

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/login')"

# Run the application
CMD ["uv", "run", "uvicorn", "alma.main:app", "--host", "0.0.0.0", "--port", "8000"]
