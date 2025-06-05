FROM python:3.10-slim

WORKDIR /app

# Instala dependências básicas
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Instala o Real-ESRGAN e requisitos da API
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos da API
COPY . .

# Baixa o modelo treinado (RealESRGAN_x4plus)
RUN python -m realesrgan.download

# Porta da API
EXPOSE 5000

CMD ["python", "app.py"]
