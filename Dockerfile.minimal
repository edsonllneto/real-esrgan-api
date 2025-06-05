# Use Python 3.11 slim - minimal and compatible
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
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

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
