# Power BI Refresh Script

Script automatizado en Python para refrescar datasets de Power BI mediante autenticación con service principal de Azure AD.

## 📋 Descripción del Proyecto

Este proyecto proporciona una solución robusta y automatizada para refrescar datasets de Power BI sin intervención manual. Utiliza un service principal de Azure AD para autenticación, permitiendo su ejecución en entornos automatizados como cron jobs, Azure DevOps pipelines, o contenedores Docker.

### Características Principales

- ✅ **Autenticación segura** con service principal de Azure AD
- ✅ **Refresco automatizado** de múltiples datasets y workspaces
- ✅ **Manejo robusto de errores** con reintentos inteligentes y backoff exponencial
- ✅ **Logging estructurado** a consola y archivo con niveles configurables
- ✅ **Configuración flexible** mediante JSON/YAML, variables de entorno o argumentos CLI
- ✅ **Soporte Docker** para ejecución portable y consistente
- ✅ **Resumen detallado** de ejecución con estadísticas de éxito/fallo
- ✅ **Monitoreo en tiempo real** del estado de refrescos con polling configurable
- ✅ **Rate limiting** automático para respetar límites de la API de Power BI

### Casos de Uso

- Automatizar refrescos nocturnos de datasets de Power BI
- Integrar refrescos en pipelines de CI/CD
- Ejecutar refrescos programados mediante cron o Task Scheduler
- Refrescar datasets después de procesos ETL
- Gestionar refrescos de múltiples workspaces desde un solo script

## 📦 Requisitos y Dependencias

### Requisitos del Sistema

- **Python**: 3.9 o superior
- **Sistema Operativo**: Linux, macOS, o Windows
- **Docker** (opcional): 20.10 o superior para ejecución en contenedor

### Requisitos de Azure y Power BI

- **Service Principal** de Azure AD con permisos configurados
- **Permisos de API**: `Dataset.Read.All` y `Dataset.ReadWrite.All`
- **Acceso a Workspaces**: El service principal debe tener rol Member o Contributor
- **Configuración del Tenant**: Service principals habilitados en Power BI Admin Portal

### Dependencias de Python

Las dependencias principales incluyen:

- `requests` - Cliente HTTP para llamadas a la API de Power BI
- `msal` - Microsoft Authentication Library para autenticación con Azure AD
- `pyyaml` - Soporte para archivos de configuración YAML
- `python-dotenv` - Carga de variables de entorno desde archivos .env

Ver `requirements.txt` para la lista completa de dependencias.


## 🚀 Instalación

### Opción 1: Instalación Local

#### Paso 1: Clonar el Repositorio

```bash
git clone <repository-url>
cd powerbi-refresh-script
```

#### Paso 2: Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

#### Paso 3: Instalar Dependencias

```bash
# Instalación básica
pip install -e .

# Instalación para desarrollo (incluye herramientas de testing)
pip install -e ".[dev]"
```

#### Paso 4: Verificar Instalación

```bash
# Verificar que el comando está disponible
powerbi-refresh --help
```

### Opción 2: Instalación con Docker

Docker proporciona una forma portable de ejecutar el script sin instalar dependencias localmente.

#### Paso 1: Construir la Imagen

```bash
# Construir imagen Docker
docker build -t powerbi-refresh:latest .

# O usar Docker Compose
docker-compose build
```

#### Paso 2: Verificar la Imagen

```bash
# Listar imágenes
docker images | grep powerbi-refresh

# Probar el comando de ayuda
docker run --rm powerbi-refresh:latest --help
```

Para instrucciones detalladas de uso con Docker, consulta la [documentación de Docker](docs/docker-usage.md).


## ⚙️ Configuración

El script soporta tres métodos de configuración con el siguiente orden de precedencia:

**CLI Arguments > Archivo de Configuración > Variables de Entorno**

### Método 1: Archivo de Configuración (Recomendado)

Crea un archivo `config.yaml` o `config.json` basado en los ejemplos proporcionados:

```bash
# Copiar archivo de ejemplo
cp config.example.yaml config.yaml

# Editar con tus valores
nano config.yaml
```

#### Ejemplo de Configuración YAML

```yaml
# Credenciales de Azure AD
azure:
  tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  client_secret: "tu-secreto-aqui"

# Workspaces y datasets
powerbi:
  workspaces:
    - id: "workspace-id-1"
      datasets:
        - "dataset-id-1"
        - "dataset-id-2"
    - id: "workspace-id-2"
      datasets: []  # Vacío = refrescar todos los datasets

# Configuración de ejecución
execution:
  poll_interval: 30      # Segundos entre verificaciones de estado
  timeout: 3600          # Timeout máximo en segundos (1 hora)
  max_retries: 3         # Número máximo de reintentos
  retry_backoff: [5, 10, 20]  # Backoff exponencial en segundos

# Configuración de logging
logging:
  level: "INFO"          # DEBUG, INFO, WARNING, ERROR
  file: "powerbi_refresh.log"  # Opcional
```

Ver `config.example.yaml` o `config.example.json` para ejemplos completos con documentación.

### Método 2: Variables de Entorno

Crea un archivo `.env` en el directorio raíz:

```bash
# Credenciales de Azure
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=tu-secreto-aqui

# Workspaces y datasets (separados por coma)
POWERBI_WORKSPACE_IDS=workspace-id-1,workspace-id-2
POWERBI_DATASET_IDS=dataset-id-1,dataset-id-2

# Configuración de ejecución
POLL_INTERVAL=30
TIMEOUT=3600
MAX_RETRIES=3
RETRY_BACKOFF=5,10,20

# Logging
LOG_LEVEL=INFO
LOG_FILE=powerbi_refresh.log
```

### Método 3: Argumentos de Línea de Comandos

Los argumentos CLI tienen la mayor precedencia y sobrescriben cualquier otra configuración:

```bash
powerbi-refresh \
  --workspace-id workspace-id-1 \
  --dataset-id dataset-id-1 \
  --dataset-id dataset-id-2 \
  --log-level DEBUG \
  --log-file debug.log
```

### Opciones de Configuración

| Parámetro | Variable de Entorno | Descripción | Valor por Defecto |
|-----------|---------------------|-------------|-------------------|
| `--config` | - | Ruta al archivo de configuración | - |
| `--workspace-id` | `POWERBI_WORKSPACE_IDS` | ID del workspace (repetible) | - |
| `--dataset-id` | `POWERBI_DATASET_IDS` | ID del dataset (repetible) | - |
| `--log-level` | `LOG_LEVEL` | Nivel de logging | `INFO` |
| `--log-file` | `LOG_FILE` | Ruta al archivo de log | - |
| `--output-format` | - | Formato de salida (text, json) | `text` |
| `--help` | - | Mostrar ayuda | - |


## 📖 Ejemplos de Uso Básico

### Ejemplo 1: Uso con Archivo de Configuración

```bash
# Ejecutar con configuración por defecto
powerbi-refresh --config config.yaml

# Ejecutar con nivel de log DEBUG
powerbi-refresh --config config.yaml --log-level DEBUG

# Salida en formato JSON
powerbi-refresh --config config.yaml --output-format json > resultado.json
```

### Ejemplo 2: Especificar Workspaces y Datasets Directamente

```bash
# Refrescar un dataset específico
powerbi-refresh \
  --workspace-id "abc-123-def-456" \
  --dataset-id "xyz-789-uvw-012"

# Refrescar múltiples datasets
powerbi-refresh \
  --workspace-id "workspace-1" \
  --dataset-id "dataset-1" \
  --dataset-id "dataset-2" \
  --dataset-id "dataset-3"

# Múltiples workspaces
powerbi-refresh \
  --workspace-id "workspace-1" \
  --workspace-id "workspace-2" \
  --dataset-id "dataset-1"
```

### Ejemplo 3: Uso con Variables de Entorno

```bash
# Configurar variables de entorno
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"

# Ejecutar sin archivo de configuración
powerbi-refresh \
  --workspace-id "workspace-id" \
  --dataset-id "dataset-id"
```

### Ejemplo 4: Ejecución Programada con Cron

Crea un script `run-refresh.sh`:

```bash
#!/bin/bash
cd /ruta/al/proyecto
source venv/bin/activate
powerbi-refresh --config config.yaml >> /var/log/powerbi-refresh.log 2>&1
```

Agrega a crontab:

```bash
# Editar crontab
crontab -e

# Ejecutar todos los días a las 6:00 AM
0 6 * * * /ruta/al/proyecto/run-refresh.sh
```

### Ejemplo 5: Salida del Script

#### Salida en Formato Texto

```
2024-01-15 10:30:00 - INFO - Starting Power BI refresh script
2024-01-15 10:30:01 - INFO - Authenticating with Azure AD
2024-01-15 10:30:02 - INFO - Authentication successful
2024-01-15 10:30:03 - INFO - Processing workspace: Sales Analytics (abc-123)
2024-01-15 10:30:04 - INFO - Starting refresh for dataset: Sales Data (xyz-789)
2024-01-15 10:30:05 - INFO - Refresh initiated, monitoring status...
2024-01-15 10:32:15 - INFO - Refresh completed successfully (duration: 130s)

=== Execution Summary ===
Total datasets: 3
Successful: 2
Failed: 1
Total duration: 245.3s

Failed datasets:
  - Marketing Data (workspace: Marketing, error: Dataset not found)
```

#### Salida en Formato JSON

```json
{
  "total_datasets": 3,
  "successful": 2,
  "failed": 1,
  "total_duration": 245.3,
  "results": [
    {
      "dataset_id": "xyz-789",
      "dataset_name": "Sales Data",
      "workspace_id": "abc-123",
      "success": true,
      "duration": 130.2,
      "start_time": "2024-01-15T10:30:04Z",
      "end_time": "2024-01-15T10:32:14Z"
    }
  ]
}
```


## 🔐 Configuración de Azure y Power BI

Para que el script funcione correctamente, debes configurar un service principal en Azure AD con los permisos necesarios en Power BI.

### Pasos Rápidos

1. **Crear Service Principal** en Azure AD
2. **Crear Grupo de Seguridad** y agregar el service principal
3. **Configurar Permisos de API** (Dataset.Read.All, Dataset.ReadWrite.All)
4. **Habilitar Service Principals** en Power BI Admin Portal
5. **Agregar Service Principal a Workspaces** con rol Member o Contributor

### Documentación Completa

Para instrucciones detalladas paso a paso con comandos de Azure CLI y PowerShell, consulta:

📚 **[Guía Completa de Configuración de Azure](docs/azure-setup.md)**

Esta guía incluye:
- Instrucciones detalladas para Azure Portal, Azure CLI y PowerShell
- Configuración de permisos y roles
- Scripts de automatización
- Solución de problemas comunes
- Verificación de la configuración

### Permisos Requeridos

| Recurso | Permiso | Descripción |
|---------|---------|-------------|
| **Azure AD** | Application Developer | Para crear service principal |
| **Power BI API** | Dataset.Read.All | Leer información de datasets |
| **Power BI API** | Dataset.ReadWrite.All | Iniciar refrescos de datasets |
| **Power BI Workspace** | Member o Contributor | Acceso al workspace y datasets |
| **Power BI Tenant** | Service principals enabled | Habilitar uso de service principals |


## 🐳 Uso con Docker

Docker proporciona una forma portable y consistente de ejecutar el script sin necesidad de instalar Python o dependencias localmente.

### Inicio Rápido con Docker Compose

1. **Configurar credenciales** en archivo `.env`:

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

2. **Configurar workspaces** en `config.yaml`:

```bash
cp config.example.yaml config.yaml
# Editar config.yaml con tus workspaces y datasets
```

3. **Ejecutar el script**:

```bash
# Ejecutar una vez
docker-compose up

# Ejecutar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Uso con Docker Run

```bash
# Con archivo de configuración
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  powerbi-refresh:latest \
  --config /app/config.yaml

# Con variables de entorno únicamente
docker run --rm \
  -e AZURE_TENANT_ID="your-tenant-id" \
  -e AZURE_CLIENT_ID="your-client-id" \
  -e AZURE_CLIENT_SECRET="your-client-secret" \
  powerbi-refresh:latest \
  --workspace-id "workspace-id" \
  --dataset-id "dataset-id"
```

### Documentación Completa de Docker

Para instrucciones detalladas sobre uso con Docker, incluyendo:
- Construcción de imágenes
- Montaje de volúmenes
- Configuración avanzada
- Casos de uso comunes
- Solución de problemas

Consulta: 📚 **[Guía de Uso con Docker](docs/docker-usage.md)**


## 🔧 Troubleshooting

### Problemas Comunes y Soluciones

#### Error: "AADSTS7000215: Invalid client secret is provided"

**Causa**: El client secret es incorrecto o ha expirado.

**Solución**:
1. Verifica que el client secret en tu configuración sea correcto
2. Si ha expirado, genera un nuevo secret en Azure Portal
3. Actualiza tu configuración con el nuevo secret

```bash
# Verificar con nivel DEBUG para más información
powerbi-refresh --config config.yaml --log-level DEBUG
```

#### Error: "Unauthorized - 401"

**Causa**: El service principal no tiene permisos suficientes.

**Solución**:
1. Verifica que el service principal esté agregado al workspace con rol Member o Contributor
2. Verifica que los permisos de API estén configurados correctamente
3. Asegúrate de que el consentimiento de administrador esté otorgado
4. Espera 15 minutos para que los cambios se propaguen

```bash
# Verificar permisos en Azure Portal
# Azure AD > App registrations > Tu aplicación > API permissions
```

#### Error: "Service principals are not enabled"

**Causa**: Los service principals no están habilitados en Power BI.

**Solución**:
1. Ve a Power BI Admin Portal > Tenant settings
2. Habilita "Allow service principals to use Power BI APIs"
3. Agrega el grupo de seguridad que contiene tu service principal
4. Espera 15 minutos para propagación

#### Error: "Dataset not found" o "Workspace not found"

**Causa**: IDs incorrectos o sin acceso.

**Solución**:
1. Verifica los IDs en Power BI Service (URL del workspace/dataset)
2. Asegúrate de usar GUIDs completos (formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
3. Verifica que el service principal tenga acceso al workspace

```bash
# Listar workspaces accesibles (requiere implementación)
powerbi-refresh --list-workspaces
```

#### Error: "RefreshTimeoutError: Refresh exceeded maximum timeout"

**Causa**: El refresco tarda más que el timeout configurado.

**Solución**:
1. Aumenta el valor de `timeout` en la configuración:

```yaml
execution:
  timeout: 7200  # 2 horas en lugar de 1
```

2. Considera refrescar datasets grandes en horarios de menor carga
3. Verifica el rendimiento del dataset en Power BI Service

#### Error: "Rate limit reached (429)"

**Causa**: Demasiadas solicitudes a la API de Power BI.

**Solución**:
- El script maneja automáticamente el rate limiting
- Espera el tiempo indicado en el mensaje
- Si ocurre frecuentemente, espacía las ejecuciones del script

```
WARNING: Rate limit reached. Waiting 60 seconds before retrying...
```

#### Error: "Connection timeout" o "Network error"

**Causa**: Problemas de conectividad de red.

**Solución**:
1. Verifica tu conexión a internet
2. Verifica que no haya firewalls bloqueando las conexiones
3. El script reintentará automáticamente (hasta 3 veces)
4. Aumenta el número de reintentos si es necesario:

```yaml
execution:
  max_retries: 5
  retry_backoff: [5, 10, 20, 40, 80]
```

### Habilitar Logging Detallado

Para obtener más información sobre errores:

```bash
# Ejecutar con nivel DEBUG
powerbi-refresh --config config.yaml --log-level DEBUG --log-file debug.log

# Revisar el archivo de log
cat debug.log
```

### Verificar Configuración

Script de verificación rápida:

```bash
# Verificar que las credenciales funcionan
python -c "
from powerbi_refresh.auth import AuthenticationService
import os

auth = AuthenticationService(
    tenant_id=os.getenv('AZURE_TENANT_ID'),
    client_id=os.getenv('AZURE_CLIENT_ID'),
    client_secret=os.getenv('AZURE_CLIENT_SECRET')
)

try:
    token = auth.get_access_token()
    print('✓ Autenticación exitosa')
except Exception as e:
    print(f'✗ Error de autenticación: {e}')
"
```

### Obtener Ayuda Adicional

Si los problemas persisten:

1. Revisa los logs con nivel DEBUG
2. Consulta la [documentación de Azure](docs/azure-setup.md)
3. Consulta la [documentación de Docker](docs/docker-usage.md)
4. Verifica la [documentación oficial de Power BI REST API](https://learn.microsoft.com/en-us/rest/api/power-bi/)
5. Abre un issue en el repositorio con:
   - Descripción del problema
   - Logs relevantes (sin credenciales)
   - Pasos para reproducir


## 📁 Estructura del Proyecto

```
powerbi-refresh-script/
├── src/
│   └── powerbi_refresh/          # Código fuente principal
│       ├── __init__.py            # Inicialización del paquete
│       ├── main.py                # Punto de entrada CLI
│       ├── config.py              # Gestor de configuración
│       ├── auth.py                # Servicio de autenticación
│       ├── powerbi_client.py      # Cliente de Power BI API
│       ├── refresh_manager.py     # Gestor de refrescos
│       ├── orchestrator.py        # Orquestador de refrescos
│       ├── retry.py               # Manejador de reintentos
│       ├── logger.py              # Configuración de logging
│       ├── models.py              # Modelos de datos
│       └── exceptions.py          # Excepciones personalizadas
│
├── tests/                         # Tests del proyecto
│   ├── unit/                      # Tests unitarios
│   │   ├── test_config.py
│   │   ├── test_auth.py
│   │   ├── test_powerbi_client.py
│   │   ├── test_refresh_manager.py
│   │   ├── test_orchestrator.py
│   │   ├── test_retry.py
│   │   └── test_logger.py
│   ├── property/                  # Property-based tests
│   │   ├── test_properties_auth.py
│   │   ├── test_properties_config.py
│   │   ├── test_properties_logging.py
│   │   └── test_properties_summary.py
│   ├── integration/               # Tests de integración
│   │   └── test_end_to_end.py
│   └── conftest.py                # Configuración de pytest
│
├── docs/                          # Documentación
│   ├── azure-setup.md             # Guía de configuración de Azure
│   └── docker-usage.md            # Guía de uso con Docker
│
├── logs/                          # Directorio de logs (generado)
│
├── .env.example                   # Ejemplo de variables de entorno
├── .gitignore                     # Archivos ignorados por git
├── config.example.json            # Ejemplo de configuración JSON
├── config.example.yaml            # Ejemplo de configuración YAML
├── docker-compose.yml             # Configuración de Docker Compose
├── Dockerfile                     # Definición de imagen Docker
├── pyproject.toml                 # Configuración del proyecto Python
├── requirements.txt               # Dependencias de producción
├── requirements-dev.txt           # Dependencias de desarrollo
└── README.md                      # Este archivo
```

## 🧪 Desarrollo y Testing

### Configurar Entorno de Desarrollo

```bash
# Clonar repositorio
git clone <repository-url>
cd powerbi-refresh-script

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar en modo desarrollo
pip install -e ".[dev]"
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo unit tests
pytest tests/unit/

# Solo property-based tests
pytest tests/property/

# Tests con cobertura
pytest --cov=powerbi_refresh --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Formateo y Linting

```bash
# Formatear código con black
black src/ tests/

# Verificar estilo con flake8
flake8 src/ tests/

# Análisis estático con pylint
pylint src/

# Type checking con mypy
mypy src/
```

### Ejecutar Property-Based Tests

Los property-based tests verifican propiedades universales del código:

```bash
# Ejecutar con estadísticas
pytest tests/property/ --hypothesis-show-statistics

# Ejecutar con más ejemplos (más exhaustivo)
pytest tests/property/ --hypothesis-max-examples=1000
```


## 📚 Documentación Adicional

### Guías Detalladas

- **[Configuración de Azure y Power BI](docs/azure-setup.md)** - Guía completa paso a paso para configurar service principal, permisos y accesos
- **[Uso con Docker](docs/docker-usage.md)** - Instrucciones detalladas para ejecutar el script en contenedores Docker

### Recursos Externos

#### Documentación Oficial de Microsoft

- [Power BI REST API Reference](https://learn.microsoft.com/en-us/rest/api/power-bi/) - Documentación completa de la API de Power BI
- [Azure AD Service Principals](https://learn.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals) - Conceptos de service principals
- [Power BI Embedded with Service Principal](https://learn.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal) - Uso de service principals en Power BI
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/) - Referencia de comandos de Azure CLI

#### Herramientas Útiles

- [Azure Portal](https://portal.azure.com) - Portal de administración de Azure
- [Power BI Service](https://app.powerbi.com) - Servicio web de Power BI
- [Microsoft Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) - Explorador de API de Microsoft Graph

### Arquitectura del Sistema

El script sigue una arquitectura modular en capas:

```
┌─────────────────────────────────────────┐
│         CLI Interface (main.py)         │
│     Argumentos y Configuración          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Orchestration Layer (orchestrator)   │
│  Coordina refrescos de múltiples        │
│  datasets y genera reportes             │
└──────┬───────────────────┬──────────────┘
       │                   │
┌──────▼──────────┐  ┌────▼──────────────┐
│  Authentication │  │  Refresh Manager  │
│     Service     │  │  Inicia y monitorea│
│  Azure AD Auth  │  │  refrescos         │
└──────┬──────────┘  └────┬──────────────┘
       │                   │
       └────────┬──────────┘
                │
┌───────────────▼──────────────────────────┐
│      Power BI API Client                 │
│  HTTP client con reintentos y rate       │
│  limiting                                │
└───────────────┬──────────────────────────┘
                │
┌───────────────▼──────────────────────────┐
│         Support Services                 │
│  Logger, Config Manager, Retry Handler   │
└──────────────────────────────────────────┘
```

## 🔒 Seguridad y Mejores Prácticas

### Gestión de Credenciales

⚠️ **IMPORTANTE**: Nunca incluyas credenciales en el código fuente o en repositorios.

**Recomendaciones**:

1. **Usa variables de entorno** para credenciales sensibles
2. **Agrega archivos de configuración a .gitignore**:
   ```
   .env
   config.yaml
   config.json
   *.log
   ```
3. **Considera Azure Key Vault** para entornos de producción
4. **Rota los client secrets** regularmente (cada 6-12 meses)
5. **Limita permisos** al mínimo necesario (principio de menor privilegio)

### Ejemplo con Azure Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Obtener credenciales desde Key Vault
credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://mi-keyvault.vault.azure.net/", credential=credential)

tenant_id = client.get_secret("azure-tenant-id").value
client_id = client.get_secret("azure-client-id").value
client_secret = client.get_secret("azure-client-secret").value
```

### Auditoría y Monitoreo

1. **Habilita logging de auditoría** en Azure AD
2. **Monitorea el uso** del service principal
3. **Configura alertas** para actividad inusual
4. **Revisa permisos** regularmente
5. **Mantén logs** de todas las ejecuciones

### Principio de Menor Privilegio

- Otorga solo los permisos mínimos necesarios
- Usa grupos de seguridad específicos, no "Entire organization"
- Limita el acceso a workspaces específicos
- Revisa y audita permisos regularmente


## 🤝 Contribuciones

Las contribuciones son bienvenidas y apreciadas. Este proyecto sigue las mejores prácticas de desarrollo colaborativo.

### Cómo Contribuir

1. **Fork el repositorio**
   ```bash
   # Haz clic en "Fork" en GitHub
   ```

2. **Clona tu fork**
   ```bash
   git clone https://github.com/tu-usuario/powerbi-refresh-script.git
   cd powerbi-refresh-script
   ```

3. **Crea una rama para tu feature**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   # o
   git checkout -b fix/correccion-bug
   ```

4. **Configura el entorno de desarrollo**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

5. **Realiza tus cambios**
   - Escribe código limpio y bien documentado
   - Agrega tests para nueva funcionalidad
   - Actualiza documentación si es necesario

6. **Ejecuta los tests**
   ```bash
   # Asegúrate de que todos los tests pasen
   pytest
   
   # Verifica el formateo
   black src/ tests/
   flake8 src/ tests/
   
   # Verifica tipos
   mypy src/
   ```

7. **Commit tus cambios**
   ```bash
   git add .
   git commit -m "feat: Agregar nueva funcionalidad X"
   # o
   git commit -m "fix: Corregir bug en Y"
   ```

8. **Push a tu fork**
   ```bash
   git push origin feature/nueva-funcionalidad
   ```

9. **Crea un Pull Request**
   - Ve a GitHub y crea un Pull Request
   - Describe claramente los cambios realizados
   - Referencia issues relacionados si aplica

### Guías de Estilo

#### Commits

Usa [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Cambios en documentación
- `test:` - Agregar o modificar tests
- `refactor:` - Refactorización de código
- `style:` - Cambios de formato (no afectan funcionalidad)
- `chore:` - Tareas de mantenimiento

Ejemplos:
```
feat: Agregar soporte para múltiples workspaces
fix: Corregir timeout en refrescos largos
docs: Actualizar guía de instalación
test: Agregar property tests para configuración
```

#### Código Python

- Sigue [PEP 8](https://pep8.org/)
- Usa [Black](https://black.readthedocs.io/) para formateo automático
- Documenta funciones con docstrings
- Agrega type hints cuando sea posible
- Mantén funciones pequeñas y enfocadas

#### Tests

- Escribe tests para toda nueva funcionalidad
- Mantén cobertura de tests > 85%
- Usa nombres descriptivos para tests
- Incluye property-based tests cuando sea apropiado

### Reportar Bugs

Si encuentras un bug, por favor abre un issue con:

1. **Descripción clara** del problema
2. **Pasos para reproducir** el bug
3. **Comportamiento esperado** vs comportamiento actual
4. **Logs relevantes** (sin credenciales)
5. **Entorno**: SO, versión de Python, versión del script
6. **Configuración** (sin credenciales)

### Solicitar Features

Para solicitar nuevas funcionalidades:

1. Abre un issue con etiqueta "enhancement"
2. Describe el caso de uso
3. Explica por qué sería útil
4. Propón una posible implementación (opcional)

### Código de Conducta

- Sé respetuoso y profesional
- Acepta críticas constructivas
- Enfócate en lo mejor para el proyecto
- Ayuda a otros contribuidores


## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

### MIT License

```
MIT License

Copyright (c) 2024 Power BI Refresh Script Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Agradecimientos

Este proyecto utiliza las siguientes bibliotecas de código abierto:

- [requests](https://requests.readthedocs.io/) - Cliente HTTP elegante y simple
- [MSAL](https://github.com/AzureAD/microsoft-authentication-library-for-python) - Microsoft Authentication Library
- [PyYAML](https://pyyaml.org/) - Parser y emitter de YAML para Python
- [pytest](https://pytest.org/) - Framework de testing
- [hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing
- [black](https://black.readthedocs.io/) - Formateador de código Python

Agradecimientos especiales a la comunidad de Power BI y Azure por la documentación y recursos.

## 📞 Soporte y Contacto

### Obtener Ayuda

- **Documentación**: Lee la [documentación completa](docs/)
- **Issues**: Busca o crea un [issue en GitHub](https://github.com/tu-usuario/powerbi-refresh-script/issues)
- **Discusiones**: Participa en [GitHub Discussions](https://github.com/tu-usuario/powerbi-refresh-script/discussions)

### Recursos Útiles

- [FAQ](docs/faq.md) - Preguntas frecuentes (si existe)
- [Troubleshooting](#-troubleshooting) - Solución de problemas comunes
- [Azure Setup Guide](docs/azure-setup.md) - Configuración de Azure
- [Docker Usage Guide](docs/docker-usage.md) - Uso con Docker

## 🗺️ Roadmap

### Versión Actual (v1.0)

- ✅ Autenticación con service principal
- ✅ Refresco de múltiples datasets
- ✅ Manejo de errores y reintentos
- ✅ Logging estructurado
- ✅ Soporte Docker
- ✅ Configuración flexible

### Futuras Mejoras (v1.1+)

- [ ] Soporte para autenticación con certificados
- [ ] Webhooks para notificaciones
- [ ] Dashboard web para monitoreo
- [ ] Integración con Azure Monitor
- [ ] Soporte para refrescos incrementales
- [ ] CLI interactivo
- [ ] Exportación de métricas a Prometheus

¿Tienes ideas para mejoras? [Abre un issue](https://github.com/tu-usuario/powerbi-refresh-script/issues/new) con la etiqueta "enhancement".

---

**Desarrollado con ❤️ para la comunidad de Power BI**

Si este proyecto te resulta útil, considera darle una ⭐ en GitHub.

