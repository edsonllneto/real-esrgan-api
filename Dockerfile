# Use Python 3.11 slim - minimal and compatible
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p bin models temp

# Download Real-ESRGAN NCNN-Vulkan with multiple fallback strategies
RUN cd bin && \
    ( \
        echo "Trying primary download..." && \
        wget -q --timeout=30 https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip && \
        unzip -q realesrgan-ncnn-vulkan-20220424-ubuntu.zip && \
        mv realesrgan-ncnn-vulkan-20220424-ubuntu/* . && \
        echo "Primary download successful" \
    ) || ( \
        echo "Primary failed, trying alternative..." && \
        rm -f *.zip && \
        curl -L -o realesrgan.zip --max-time 30 https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip && \
        unzip -q realesrgan.zip && \
        mv realesrgan-ncnn-vulkan-20220424-ubuntu/* . && \
        echo "Alternative download successful" \
    ) || ( \
        echo "Downloads failed, using git clone..." && \
        rm -f *.zip && \
        git clone --depth 1 https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan.git temp_repo && \
        find temp_repo -name "*.bin" -exec cp {} ../models/ \; && \
        find temp_repo -name "*.param" -exec cp {} ../models/ \; && \
        echo "#!/bin/bash" > realesrgan-ncnn-vulkan && \
        echo "echo 'Binary placeholder - using python fallback'" >> realesrgan-ncnn-vulkan && \
        echo "exit 1" >> realesrgan-ncnn-vulkan && \
        rm -rf temp_repo && \
        echo "Git fallback completed" \
    ) && \
    chmod +x realesrgan-ncnn-vulkan && \
    rm -rf realesrgan-ncnn-vulkan-20220424-ubuntu* *.zip && \
    cd ..

# Move models to models directory (if they exist)
RUN find bin -name "*.bin" -exec mv {} models/ \; 2>/dev/null || true && \
    find bin -name "*.param" -exec mv {} models/ \; 2>/dev/null || true && \
    mv bin/models-Real-ESRGAN/* models/ 2>/dev/null || true && \
    mv bin/models-DF2K/* models/ 2>/dev/null || true && \
    rm -rf bin/models-* || true

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
