FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY checkmate/ ./checkmate/
COPY enterprise_checkmate.py .
COPY setup.py .
COPY pyproject.toml .
COPY README.md .

# Install package in editable mode
RUN pip install -e .

# Create directories for results
RUN mkdir -p /app/runs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set entrypoint
ENTRYPOINT ["python", "enterprise_checkmate.py"]

# Default command (show help)
CMD ["--help"]
