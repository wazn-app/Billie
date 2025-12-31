# Billie MVP - Invoice Processing System
# Production Dockerfile for FastAPI Backend with PaddleOCR

# Use Python 3.11 slim base image for lightweight footprint
FROM python:3.11-slim

# Set environment variables for proper logging and configuration
ENV PYTHONUNBUFFERED=1 \
    UPLOAD_DIR=/app/uploads \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for PaddleOCR and image processing
# - libgomp1: OpenMP runtime library required by paddlepaddle
# - libgl1-mesa-glx: OpenGL library for image processing
# - libglib2.0-0: GLib library
# - poppler-utils: for pdf2image (PDF to image conversion)
# - curl: for health checks
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with no cache for smaller image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend application files
COPY . .

# Create uploads directory for file storage
RUN mkdir -p /app/uploads

# Expose port 8000 for FastAPI application
EXPOSE 8000

# Health check endpoint - verifies the application is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]