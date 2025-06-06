# Fixed Dockerfile with staged dependency installation
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including git and build tools
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libgcc-s1 \
    libstdc++6 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    git \
    build-essential \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements files
COPY requirements-core.txt requirements-pytorch.txt requirements-ml.txt ./

# STAGE 1: Install core dependencies from PyPI (always succeeds)
RUN echo "=== Installing core dependencies ===" && \
    pip install --no-cache-dir -r requirements-core.txt

# STAGE 2: Install PyTorch with correct index (always succeeds)
RUN echo "=== Installing PyTorch ===" && \
    pip install --no-cache-dir -r requirements-pytorch.txt

# STAGE 3: Install ML dependencies (graceful fallback if fails)
RUN echo "=== Installing ML dependencies ===" && \
    pip install --no-cache-dir -r requirements-ml.txt || \
    echo "Some ML dependencies failed, API will use PIL fallback"

# STAGE 4: Try to install Real-ESRGAN from git (optional)
RUN echo "=== Attempting Real-ESRGAN from git ===" && \
    pip install --no-cache-dir git+https://github.com/xinntao/Real-ESRGAN.git || \
    echo "Real-ESRGAN git install failed, using PyPI version"

# Create necessary directories
RUN mkdir -p models temp

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Environment variables for better performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Health check with longer startup time
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
