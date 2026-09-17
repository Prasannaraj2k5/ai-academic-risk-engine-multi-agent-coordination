# Multi-stage Python 3.11 production container
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Generate synthetic datasets and seed database during image build
RUN python data/generate_datasets.py

EXPOSE 8000

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
