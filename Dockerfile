FROM python:3.12-slim 
# Requisito para o Django>=6.0.0,<7.0.0 (./requirements.txt)
# (https://docs.djangoproject.com/en/6.0/releases/6.0/#python-compatibility)

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
# Para evitar conflito entre bytecode gerado no container com o que está espelhado fora dele
# (./docker-compose.yml l31)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instala dependências do sistema necessárias para o PostgreSQL e compilação
RUN apt-get update && apt-get install -y \
    build-essential \
    # libpq-dev \ # Caso vá utilizar o Postgres
    && rm -rf /var/lib/apt/lists/*

# Instala dependências do projeto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Expõe a porta do Django
EXPOSE 8000