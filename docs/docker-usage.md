# Guía de Uso con Docker

Esta guía explica cómo ejecutar el Power BI Refresh Script utilizando Docker y Docker Compose.

## Tabla de Contenidos

- [Prerrequisitos](#prerrequisitos)
- [Construcción de la Imagen](#construcción-de-la-imagen)
- [Ejecución con Docker Compose (Recomendado)](#ejecución-con-docker-compose-recomendado)
- [Ejecución con Docker Run (Alternativa)](#ejecución-con-docker-run-alternativa)
- [Opciones de Configuración](#opciones-de-configuración)
- [Montaje de Volúmenes](#montaje-de-volúmenes)
- [Casos de Uso Comunes](#casos-de-uso-comunes)
- [Solución de Problemas](#solución-de-problemas)

## Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

- **Docker**: Versión 20.10 o superior
  - [Instalar Docker en Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Instalar Docker en Mac](https://docs.docker.com/desktop/install/mac-install/)
  - [Instalar Docker en Linux](https://docs.docker.com/engine/install/)

- **Docker Compose**: Versión 2.0 o superior (incluido con Docker Desktop)
  - Verificar instalación: `docker-compose --version`

## Construcción de la Imagen

### Opción 1: Construcción Manual

Para construir la imagen Docker manualmente:

```bash
# Desde el directorio raíz del proyecto
docker build -t powerbi-refresh:latest .
```

Esto creará una imagen llamada `powerbi-refresh` con la etiqueta `latest`.

### Opción 2: Construcción con Docker Compose

Docker Compose construirá la imagen automáticamente la primera vez que ejecutes el servicio:

```bash
docker-compose build
```

Para forzar una reconstrucción (por ejemplo, después de actualizar el código):

```bash
docker-compose build --no-cache
```

## Ejecución con Docker Compose (Recomendado)

Docker Compose simplifica la ejecución del script al gestionar configuración, volúmenes y variables de entorno.

### Configuración Inicial

1. **Crear archivo de configuración**: Copia el archivo de ejemplo y ajústalo a tus necesidades:

```bash
cp config.example.yaml config.yaml
```

2. **Editar `config.yaml`**: Configura tus workspaces y datasets:

```yaml
azure:
  tenant_id: "${AZURE_TENANT_ID}"
  client_id: "${AZURE_CLIENT_ID}"
  client_secret: "${AZURE_CLIENT_SECRET}"

powerbi:
  workspaces:
    - id: "tu-workspace-id-1"
      datasets: ["dataset-id-1", "dataset-id-2"]
    - id: "tu-workspace-id-2"
      datasets: []

execution:
  poll_interval: 30
  timeout: 3600
  max_retries: 3

logging:
  level: "INFO"
  file: "/app/logs/powerbi_refresh.log"
```

3. **Configurar variables de entorno**: Crea un archivo `.env` en el directorio raíz:

```bash
# .env
AZURE_TENANT_ID=tu-tenant-id
AZURE_CLIENT_ID=tu-client-id
AZURE_CLIENT_SECRET=tu-client-secret
```

### Ejecución Básica

```bash
# Ejecutar el script una vez
docker-compose up

# Ejecutar en modo detached (segundo plano)
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Detener y eliminar el contenedor
docker-compose down
```

### Ejecución con Argumentos Personalizados

Puedes sobrescribir el comando por defecto:

```bash
# Ejecutar con nivel de log DEBUG
docker-compose run --rm powerbi-refresh --config /app/config.yaml --log-level DEBUG

# Ejecutar para un workspace específico
docker-compose run --rm powerbi-refresh --workspace-id <WORKSPACE_ID> --dataset-id <DATASET_ID>

# Ver ayuda
docker-compose run --rm powerbi-refresh --help
```

## Ejecución con Docker Run (Alternativa)

Si prefieres no usar Docker Compose, puedes ejecutar el contenedor directamente con `docker run`.

### Construcción de la Imagen

```bash
docker build -t powerbi-refresh:latest .
```

### Ejecución Básica

```bash
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  -e AZURE_TENANT_ID="tu-tenant-id" \
  -e AZURE_CLIENT_ID="tu-client-id" \
  -e AZURE_CLIENT_SECRET="tu-client-secret" \
  powerbi-refresh:latest \
  --config /app/config.yaml
```

### Explicación de Opciones

- `--rm`: Elimina el contenedor automáticamente después de la ejecución
- `-v $(pwd)/config.yaml:/app/config.yaml:ro`: Monta el archivo de configuración (solo lectura)
- `-v $(pwd)/logs:/app/logs`: Monta el directorio de logs (lectura/escritura)
- `-e VARIABLE=valor`: Define variables de entorno
- `powerbi-refresh:latest`: Nombre de la imagen
- `--config /app/config.yaml`: Argumentos para el script

### Ejecución con Variables de Entorno Únicamente

```bash
docker run --rm \
  -v $(pwd)/logs:/app/logs \
  -e AZURE_TENANT_ID="tu-tenant-id" \
  -e AZURE_CLIENT_ID="tu-client-id" \
  -e AZURE_CLIENT_SECRET="tu-client-secret" \
  -e POWERBI_WORKSPACE_IDS="workspace-id-1,workspace-id-2" \
  -e POWERBI_DATASET_IDS="dataset-id-1,dataset-id-2" \
  -e LOG_LEVEL="INFO" \
  powerbi-refresh:latest \
  --workspace-id workspace-id-1 \
  --dataset-id dataset-id-1
```

## Opciones de Configuración

El script puede configurarse mediante tres métodos (en orden de precedencia):

1. **Argumentos de línea de comandos** (mayor prioridad)
2. **Archivo de configuración** (YAML o JSON)
3. **Variables de entorno** (menor prioridad)

### Variables de Entorno Soportadas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `AZURE_TENANT_ID` | ID del tenant de Azure AD | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_ID` | ID del cliente (service principal) | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_SECRET` | Secreto del cliente | `tu-secreto-aqui` |
| `POWERBI_WORKSPACE_IDS` | IDs de workspaces (separados por coma) | `id1,id2,id3` |
| `POWERBI_DATASET_IDS` | IDs de datasets (separados por coma) | `id1,id2,id3` |
| `POLL_INTERVAL` | Intervalo de polling en segundos | `30` |
| `TIMEOUT` | Timeout máximo en segundos | `3600` |
| `MAX_RETRIES` | Número máximo de reintentos | `3` |
| `LOG_LEVEL` | Nivel de logging | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE` | Ruta al archivo de log | `/app/logs/powerbi_refresh.log` |

### Argumentos de Línea de Comandos

```bash
--config PATH              Ruta al archivo de configuración
--workspace-id ID          ID del workspace (puede repetirse)
--dataset-id ID            ID del dataset (puede repetirse)
--log-level LEVEL          Nivel de logging (DEBUG, INFO, WARNING, ERROR)
--log-file PATH            Ruta al archivo de log
--output-format FORMAT     Formato de salida (text, json)
--help                     Mostrar ayuda
```

## Montaje de Volúmenes

Los volúmenes permiten compartir archivos entre el host y el contenedor.

### Volumen de Configuración

Monta tu archivo de configuración en modo solo lectura:

```yaml
volumes:
  - ./config.yaml:/app/config.yaml:ro
```

O con `docker run`:

```bash
-v $(pwd)/config.yaml:/app/config.yaml:ro
```

### Volumen de Logs

Monta un directorio para persistir los logs:

```yaml
volumes:
  - ./logs:/app/logs
```

O con `docker run`:

```bash
-v $(pwd)/logs:/app/logs
```

Los logs se guardarán en el directorio `logs` de tu máquina host.

### Volumen de Configuración Alternativa

Si tienes múltiples archivos de configuración:

```bash
# Montar directorio completo
-v $(pwd)/configs:/app/configs:ro

# Usar configuración específica
docker run ... powerbi-refresh:latest --config /app/configs/produccion.yaml
```

## Casos de Uso Comunes

### 1. Ejecución Única con Configuración

```bash
# Con Docker Compose
docker-compose up

# Con Docker Run
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  powerbi-refresh:latest \
  --config /app/config.yaml
```

### 2. Ejecución Programada con Cron

Crea un script `run-refresh.sh`:

```bash
#!/bin/bash
cd /ruta/al/proyecto
docker-compose up
```

Agrega a crontab:

```bash
# Ejecutar todos los días a las 6:00 AM
0 6 * * * /ruta/al/proyecto/run-refresh.sh >> /var/log/powerbi-refresh-cron.log 2>&1
```

### 3. Ejecución con Nivel de Log DEBUG

```bash
# Con Docker Compose
docker-compose run --rm powerbi-refresh --config /app/config.yaml --log-level DEBUG

# Con Docker Run
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  powerbi-refresh:latest \
  --config /app/config.yaml --log-level DEBUG
```

### 4. Refrescar Dataset Específico

```bash
# Con Docker Compose
docker-compose run --rm powerbi-refresh \
  --workspace-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --dataset-id "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"

# Con Docker Run
docker run --rm \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  powerbi-refresh:latest \
  --workspace-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --dataset-id "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
```

### 5. Salida en Formato JSON

```bash
docker-compose run --rm powerbi-refresh \
  --config /app/config.yaml \
  --output-format json > resultado.json
```

### 6. Ejecución en Modo Interactivo (Debugging)

```bash
# Abrir shell dentro del contenedor
docker-compose run --rm --entrypoint /bin/bash powerbi-refresh

# Dentro del contenedor, ejecutar manualmente
powerbi-refresh --config /app/config.yaml --log-level DEBUG
```

### 7. Múltiples Workspaces y Datasets

```bash
docker-compose run --rm powerbi-refresh \
  --workspace-id "workspace-1" \
  --workspace-id "workspace-2" \
  --dataset-id "dataset-1" \
  --dataset-id "dataset-2" \
  --dataset-id "dataset-3"
```

## Solución de Problemas

### Problema: Error de Autenticación

**Síntoma**: `AuthenticationError: Failed to authenticate with Azure AD`

**Solución**:
1. Verifica que las credenciales en `.env` o `config.yaml` sean correctas
2. Asegúrate de que el service principal tenga los permisos necesarios
3. Verifica que las variables de entorno se estén pasando correctamente:

```bash
# Verificar variables dentro del contenedor
docker-compose run --rm powerbi-refresh env | grep AZURE
```

### Problema: No se Encuentran los Logs

**Síntoma**: Los logs no aparecen en el directorio `logs/`

**Solución**:
1. Verifica que el volumen esté montado correctamente en `docker-compose.yml`
2. Asegúrate de que el directorio `logs/` exista en el host:

```bash
mkdir -p logs
chmod 755 logs
```

3. Verifica la configuración de `LOG_FILE` en tu configuración

### Problema: Archivo de Configuración No Encontrado

**Síntoma**: `ConfigurationError: Config file not found`

**Solución**:
1. Verifica que el archivo `config.yaml` exista en el directorio raíz
2. Asegúrate de que el volumen esté montado correctamente:

```bash
# Verificar montaje
docker-compose config
```

3. Usa ruta absoluta si es necesario:

```bash
-v /ruta/completa/config.yaml:/app/config.yaml:ro
```

### Problema: Permisos Denegados en Workspace

**Síntoma**: `PermissionError: Service principal does not have access to workspace`

**Solución**:
1. Verifica que el service principal esté agregado al workspace con rol Member o Admin
2. Consulta la [documentación de configuración de Azure](./azure-setup.md) para más detalles
3. Verifica los permisos con nivel de log DEBUG:

```bash
docker-compose run --rm powerbi-refresh --config /app/config.yaml --log-level DEBUG
```

### Problema: Timeout en Refresco

**Síntoma**: `RefreshTimeoutError: Refresh exceeded maximum timeout`

**Solución**:
1. Aumenta el valor de `TIMEOUT` en la configuración:

```yaml
execution:
  timeout: 7200  # 2 horas
```

2. O mediante variable de entorno:

```bash
-e TIMEOUT=7200
```

### Problema: Rate Limiting (429)

**Síntoma**: `WARNING: Rate limit reached. Waiting 60 seconds...`

**Solución**:
- Esto es normal y el script manejará automáticamente el rate limiting
- Si ocurre frecuentemente, considera espaciar las ejecuciones
- Reduce el número de datasets procesados simultáneamente

### Problema: Imagen No Se Actualiza

**Síntoma**: Los cambios en el código no se reflejan en el contenedor

**Solución**:
1. Reconstruye la imagen sin caché:

```bash
docker-compose build --no-cache
```

2. O con Docker:

```bash
docker build --no-cache -t powerbi-refresh:latest .
```

### Problema: Contenedor Se Queda Colgado

**Síntoma**: El contenedor no responde o no termina

**Solución**:
1. Detén el contenedor forzadamente:

```bash
docker-compose down -t 1
```

2. O con Docker:

```bash
docker stop powerbi-refresh-script
docker rm powerbi-refresh-script
```

3. Verifica los logs para identificar el problema:

```bash
docker-compose logs
```

### Verificación de Salud del Contenedor

Para verificar que el contenedor funciona correctamente:

```bash
# Verificar que la imagen se construyó correctamente
docker images | grep powerbi-refresh

# Probar el comando de ayuda
docker-compose run --rm powerbi-refresh --help

# Verificar variables de entorno
docker-compose run --rm powerbi-refresh env

# Ejecutar en modo DEBUG para diagnóstico
docker-compose run --rm powerbi-refresh --config /app/config.yaml --log-level DEBUG
```

## Recursos Adicionales

- [Documentación de Configuración de Azure](./azure-setup.md)
- [README Principal](../README.md)
- [Documentación de Docker](https://docs.docker.com/)
- [Documentación de Docker Compose](https://docs.docker.com/compose/)
- [Power BI REST API](https://learn.microsoft.com/en-us/rest/api/power-bi/)

## Notas de Seguridad

⚠️ **Importante**: Nunca incluyas credenciales directamente en `docker-compose.yml` o en el código fuente.

**Mejores prácticas**:
- Usa archivos `.env` y agrégalos a `.gitignore`
- Considera usar Azure Key Vault para gestión de secretos
- En producción, usa Docker Secrets o variables de entorno del sistema
- Limita los permisos del service principal al mínimo necesario

```bash
# Ejemplo de .gitignore
.env
config.yaml
logs/
*.log
```
