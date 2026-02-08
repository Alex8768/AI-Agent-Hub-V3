# Multi-stage Dockerfile for AI Agent Hub V3
# ARCHITECTURE_V3 Implementation

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for modern Python packaging
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.cargo/bin/uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./
COPY requirements*.txt ./

# Create virtual environment and install dependencies
RUN uv venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN uv pip install --system --no-cache -r requirements.txt

# Stage 2: Runtime for development
FROM python:3.12-slim AS development

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-rus \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/workspace /app/templates

# Create non-root user
RUN groupadd -r agent && useradd -r -g agent agent \
    && chown -R agent:agent /app
USER agent

# Expose ports
EXPOSE 8000 9091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command for development
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Runtime for production
FROM python:3.12-slim AS production

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy only necessary files
COPY src/ ./src/
COPY config/ ./config/
COPY docker/ ./docker/
COPY pyproject.toml ./

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/workspace /app/templates \
    && chmod -R 755 /app

# Create non-root user
RUN groupadd -r agent && useradd -r -g agent agent \
    && chown -R agent:agent /app
USER agent

# Expose ports
EXPOSE 8000 9091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command for production
CMD ["gunicorn", "src.api.main:app", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--workers", "4", \
     "--access-logfile", "-", "--error-logfile", "-"]
