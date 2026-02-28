# Dockerfile para Power BI Refresh Script
# Usa imagen base de Python 3.9 slim para menor tamaño

FROM python:3.9-slim

# Metadatos de la imagen
LABEL maintainer="Power BI Automation Team"
LABEL description="Script automatizado para refrescar datasets de Power BI"
LABEL version="1.0.0"

# Establecer variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias primero (para aprovechar caché de Docker)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY src/powerbi_refresh ./powerbi_refresh
COPY pyproject.toml .
COPY README.md .

# Instalar el paquete en modo editable
RUN pip install --no-cache-dir -e .

# Crear directorio para logs
RUN mkdir -p /app/logs

# Definir punto de entrada
ENTRYPOINT ["powerbi-refresh"]

# Comando por defecto (puede ser sobrescrito)
CMD ["--help"]
