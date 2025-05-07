FROM python:3.11-slim

# Instala pacotes de sistema necessários
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    libxml2-dev \
    libxslt1-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia apenas o requirements.txt e instala dependências
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Comando padrão (ajuste conforme necessário)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
