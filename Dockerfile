# Use Python 3.11 slim image for smaller footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for image processing and Vulkan
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libvulkan1 \
    vulkan-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p bin models temp

# Download and setup Real-ESRGAN NCNN-Vulkan
RUN cd bin && \
    wget -q https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip && \
    unzip -q realesrgan-ncnn-vulkan-20220424-ubuntu.zip && \
    mv realesrgan-ncnn-vulkan-20220424-ubuntu/* . && \
    chmod +x realesrgan-ncnn-vulkan && \
    rm -rf realesrgan-ncnn-vulkan-20220424-ubuntu* && \
    cd ..

# Move models to models directory
RUN mv bin/models-Real-ESRGAN/* models/ 2>/dev/null || true && \
    mv bin/models-DF2K/* models/ 2>/dev/null || true && \
    rm -rf bin/models-*

# Copy application code
COPY app/ ./app/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Environment variables for optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV OMP_NUM_THREADS=2
ENV MKL_NUM_THREADS=2

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
