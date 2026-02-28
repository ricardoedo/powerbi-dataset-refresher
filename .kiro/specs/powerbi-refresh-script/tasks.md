# Plan de Implementación: Power BI Refresh Script

## Descripción General

Este plan implementa un script automatizado en Python para refrescar datasets de Power BI mediante autenticación con service principal de Azure. La implementación sigue una arquitectura modular en capas con manejo robusto de errores, logging estructurado y soporte para ejecución en Docker.

## Tareas

- [x] 1. Configurar estructura del proyecto y dependencias
  - Crear estructura de directorios (src/, tests/, docs/)
  - Crear requirements.txt con dependencias principales (requests, pyyaml, hypothesis, pytest)
  - Crear requirements-dev.txt con herramientas de desarrollo
  - Crear setup.py o pyproject.toml para instalación del paquete
  - _Requisitos: 8.2_

- [x] 2. Implementar modelos de datos y excepciones personalizadas
  - [x] 2.1 Crear módulo de excepciones (exceptions.py)
    - Implementar PowerBIScriptError como excepción base
    - Implementar AuthenticationError, PowerBIAPIError, ConfigurationError
    - Implementar PermissionError y RefreshTimeoutError
    - _Requisitos: 1.2, 2.4, 3.3, 6.1_
  
  - [x] 2.2 Crear módulo de modelos de datos (models.py)
    - Implementar enumeraciones RefreshStatus y LogLevel
    - Implementar dataclasses: Dataset, Workspace, RefreshRequest, RefreshHistory
    - Implementar dataclasses: RefreshResult y ExecutionSummary con métodos to_dict() y to_text()
    - _Requisitos: 2.1, 2.3, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 3. Implementar gestión de configuración
  - [x] 3.1 Crear módulo de configuración (config.py)
    - Implementar dataclass Config con todos los campos necesarios
    - Implementar ConfigManager.load() para cargar desde JSON/YAML y variables de entorno
    - Implementar ConfigManager.validate() para validar configuración
    - Implementar precedencia: CLI > archivo > variables de entorno
    - _Requisitos: 1.3, 7.1, 7.2, 7.3, 7.4_
  
  - [x] 3.2 Escribir property test para configuración
    - **Property 15: Carga de configuración desde múltiples formatos**
    - **Property 16: Precedencia de argumentos CLI**
    - **Property 17: Validación de configuración requerida**
    - **Valida: Requisitos 7.1, 7.2, 7.3**
  
  - [x] 3.3 Crear archivo de configuración de ejemplo (config.example.json)
    - Incluir todos los campos con valores de ejemplo
    - Documentar cada campo con comentarios
    - _Requisitos: 7.5_

- [x] 4. Checkpoint - Validar estructura base
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [x] 5. Implementar servicio de logging
  - [x] 5.1 Crear módulo de logging (logger.py)
    - Implementar ScriptLogger.setup() con handlers para consola y archivo
    - Configurar formato de logs con timestamp, nivel y mensaje
    - Implementar soporte para niveles configurables (DEBUG, INFO, WARNING, ERROR)
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 5.2 Escribir property tests para logging
    - **Property 8: Estructura de logs completa**
    - **Property 9: Stack trace en errores**
    - **Property 10: Respeto de nivel de logging**
    - **Property 11: Registro de duración de refrescos**
    - **Valida: Requisitos 4.1, 4.2, 4.3, 4.5**

- [x] 6. Implementar manejador de reintentos
  - [x] 6.1 Crear módulo de reintentos (retry.py)
    - Implementar RetryHandler con configuración de max_retries y backoff_delays
    - Implementar execute_with_retry() con backoff exponencial
    - Implementar should_retry() para clasificar excepciones reintentables
    - Implementar handle_rate_limit() para manejar respuestas 429
    - _Requisitos: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 6.2 Escribir property tests para reintentos
    - **Property 12: Reintentos en errores transitorios**
    - **Property 13: Continuación tras fallos de reintentos**
    - **Property 14: Respeto de Retry-After en rate limiting**
    - **Valida: Requisitos 6.1, 6.3, 6.4**

- [ ] 7. Implementar servicio de autenticación
  - [x] 7.1 Crear módulo de autenticación (auth.py)
    - Implementar AuthenticationService.__init__() con credenciales
    - Implementar get_access_token() con caché y renovación automática
    - Implementar is_token_valid() para verificar validez del token
    - Integrar con RetryHandler para reintentos en errores de red
    - _Requisitos: 1.1, 1.2, 1.4_
  
  - [x] 7.2 Escribir property tests para autenticación
    - **Property 1: Autenticación con credenciales válidas**
    - **Property 2: Rechazo de credenciales inválidas**
    - **Valida: Requisitos 1.1, 1.2**
  
  - [x] 7.3 Escribir unit tests para autenticación
    - Test de autenticación exitosa con credenciales válidas
    - Test de fallo con credenciales inválidas
    - Test de caché y reutilización de token
    - Test de renovación cuando el token expira
    - Test de fallo después de 3 intentos
    - _Requisitos: 1.1, 1.2, 1.4_

- [x] 8. Checkpoint - Validar servicios base
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [-] 9. Implementar cliente de Power BI API
  - [x] 9.1 Crear módulo de cliente (powerbi_client.py)
    - Implementar PowerBIClient.__init__() con AuthenticationService y RetryHandler
    - Implementar list_datasets() para listar datasets en un workspace
    - Implementar start_refresh() para iniciar refresco de dataset
    - Implementar get_refresh_status() para consultar estado de refresco
    - Manejar errores de API con excepciones personalizadas
    - _Requisitos: 2.1, 3.2, 3.3, 3.4_
  
  - [x] 9.2 Escribir property tests para cliente de API
    - **Property 3: Inicio de refresco para datasets válidos**
    - **Property 6: Validación de permisos en workspace**
    - **Property 7: Listado completo de datasets**
    - **Valida: Requisitos 2.1, 3.2, 3.3, 3.4**
  
  - [x] 9.3 Escribir unit tests para cliente de API
    - Test de list_datasets con respuesta exitosa
    - Test de start_refresh con respuesta 202 Accepted
    - Test de get_refresh_status con diferentes estados
    - Test de manejo de error 401 (sin permisos)
    - Test de manejo de error 429 (rate limit)
    - Test de manejo de errores 5xx con reintentos
    - _Requisitos: 2.1, 3.2, 3.3, 3.4, 6.1, 6.4_

- [ ] 10. Implementar gestor de refrescos
  - [x] 10.1 Crear módulo de gestor de refrescos (refresh_manager.py)
    - Implementar RefreshManager.__init__() con PowerBIClient y configuración
    - Implementar refresh_dataset() para ejecutar refresco completo
    - Implementar _poll_refresh_status() para monitorear estado cada 30 segundos
    - Manejar timeouts de refresco según configuración
    - Retornar RefreshResult con todos los detalles
    - _Requisitos: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 10.2 Escribir property tests para gestor de refrescos
    - **Property 4: Registro de resultados de refresco**
    - **Valida: Requisitos 2.3, 2.4**
  
  - [x] 10.3 Escribir unit tests para gestor de refrescos
    - Test de refresco exitoso con polling
    - Test de refresco fallido con mensaje de error
    - Test de timeout de refresco
    - Test de polling cada 30 segundos
    - Test de registro de duración
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 4.5_

- [ ] 11. Implementar orquestador de refrescos
  - [x] 11.1 Crear módulo de orquestador (orchestrator.py)
    - Implementar RefreshOrchestrator.__init__() con Config, RefreshManager y Logger
    - Implementar execute() para procesar todos los datasets configurados
    - Implementar lógica para continuar tras fallos individuales
    - Generar ExecutionSummary con todos los resultados
    - _Requisitos: 2.5, 6.3, 9.1, 9.2, 9.3, 9.4_
  
  - [x] 11.2 Escribir property tests para orquestador
    - **Property 5: Procesamiento de múltiples datasets**
    - **Property 18: Completitud del resumen de ejecución**
    - **Property 19: Detalles de datasets fallidos en resumen**
    - **Property 20: Serialización JSON del resumen**
    - **Valida: Requisitos 2.5, 9.1, 9.2, 9.3, 9.4, 9.5**
  
  - [x] 11.3 Escribir unit tests para orquestador
    - Test de ejecución con todos los datasets exitosos
    - Test de ejecución con resultados mixtos (éxitos y fallos)
    - Test de continuación tras fallo de un dataset
    - Test de resumen en formato texto
    - Test de resumen en formato JSON
    - _Requisitos: 2.5, 6.3, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 12. Checkpoint - Validar lógica de negocio
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [ ] 13. Implementar interfaz CLI
  - [x] 13.1 Crear módulo principal (main.py)
    - Implementar parseo de argumentos con argparse
    - Implementar main() que coordina carga de config, autenticación y ejecución
    - Implementar manejo de códigos de salida (0, 1, 2)
    - Implementar salida de resumen en formato texto o JSON según configuración
    - _Requisitos: 7.2, 9.5_
  
  - [x] 13.2 Escribir unit tests para CLI
    - Test de parseo de argumentos
    - Test de código de salida 0 (éxito total)
    - Test de código de salida 1 (error fatal)
    - Test de código de salida 2 (éxito parcial)
    - Test de salida en formato texto
    - Test de salida en formato JSON
    - _Requisitos: 7.2, 9.5_

- [ ] 14. Crear documentación de configuración de Azure
  - [x] 14.1 Crear documento de configuración (docs/azure-setup.md)
    - Documentar creación de service principal en Azure AD
    - Documentar creación y configuración de grupo de seguridad
    - Documentar cómo agregar service principal al grupo
    - Documentar habilitación de service principals en Power BI tenant
    - Documentar permisos de API necesarios
    - Documentar roles necesarios en workspaces
    - Incluir comandos de Azure CLI y PowerShell
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [ ] 15. Crear soporte para Docker
  - [x] 15.1 Crear Dockerfile
    - Usar imagen base de Python 3.9+
    - Instalar dependencias desde requirements.txt
    - Configurar directorio de trabajo
    - Definir punto de entrada para ejecutar el script
    - _Requisitos: 8.1, 8.2_
  
  - [x] 15.2 Crear docker-compose.yml
    - Configurar servicio para el script
    - Configurar volúmenes para configuración y logs
    - Configurar variables de entorno
    - _Requisitos: 8.3_
  
  - [x] 15.3 Documentar uso de Docker
    - Crear sección en README.md con instrucciones de Docker
    - Incluir comandos para construir imagen
    - Incluir comandos para ejecutar contenedor
    - Incluir ejemplos de paso de configuración
    - _Requisitos: 8.4, 8.5_

- [ ] 16. Crear documentación principal
  - [x] 16.1 Crear README.md
    - Incluir descripción del proyecto
    - Incluir requisitos y dependencias
    - Incluir instrucciones de instalación
    - Incluir ejemplos de uso básico
    - Incluir referencia a documentación de Azure
    - Incluir instrucciones de Docker
    - Incluir sección de troubleshooting
    - _Requisitos: Todos_
  
  - [x] 16.2 Crear archivo de ejemplo de configuración
    - Ya creado en tarea 3.3, verificar completitud
    - _Requisitos: 7.5_

- [x] 17. Checkpoint final - Validación completa
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [x] 18. Escribir tests de integración end-to-end
  - Crear test que simule ejecución completa con mocks
  - Test con múltiples datasets (éxitos y fallos)
  - Test con autenticación, reintentos y resumen
  - Verificar que el flujo completo funciona correctamente
  - _Requisitos: Todos_

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental del progreso
- Los property tests validan propiedades universales de correctitud
- Los unit tests validan ejemplos específicos y casos borde
- La implementación sigue el diseño modular en capas especificado
- Python es el lenguaje de implementación según el diseño
