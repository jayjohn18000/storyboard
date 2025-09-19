FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements-temporal.txt /app/
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-temporal.txt
RUN pip install --no-cache-dir -e .

# Copy application code
COPY services/ /app/services/
COPY config/ /app/config/

# Create non-root user
RUN useradd -m -u 1000 bridge && chown -R bridge:bridge /app
USER bridge

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Start the Temporal event bridge
CMD ["python", "scripts/start_temporal_event_bridge.py"]
