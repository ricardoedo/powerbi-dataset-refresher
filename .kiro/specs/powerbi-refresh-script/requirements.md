# Documento de Requisitos

## Introducción

Este documento define los requisitos para un script automatizado que refresca informes de Power BI utilizando la API de Power BI. El script debe autenticarse mediante un service principal de Azure y proporcionar documentación completa del proceso de configuración de permisos necesarios.

## Glosario

- **Script_Refresco**: El script de Python que ejecuta el refresco de informes de Power BI
- **Power_BI_API**: La API REST de Power BI utilizada para operaciones de refresco
- **Service_Principal**: La identidad de aplicación de Azure AD utilizada para autenticación
- **Tenant_Azure**: El inquilino de Azure Active Directory que contiene los recursos
- **Grupo_Seguridad**: El grupo de seguridad de Azure AD que contiene el service principal
- **Dataset**: El conjunto de datos de Power BI que debe ser refrescado
- **Workspace**: El espacio de trabajo de Power BI que contiene los datasets
- **Configuración_Tenant**: Los ajustes a nivel de tenant de Power BI que permiten el uso de service principals

## Requisitos

### Requisito 1: Autenticación con Service Principal

**User Story:** Como administrador de sistemas, quiero que el script se autentique usando un service principal, para que pueda ejecutarse de forma automatizada sin intervención humana.

#### Criterios de Aceptación

1. CUANDO el Script_Refresco se ejecuta, EL Script_Refresco DEBERÁ autenticarse con la Power_BI_API usando las credenciales del Service_Principal
2. CUANDO las credenciales del Service_Principal son inválidas, EL Script_Refresco DEBERÁ retornar un mensaje de error descriptivo indicando el problema de autenticación
3. EL Script_Refresco DEBERÁ leer las credenciales desde variables de entorno o archivo de configuración
4. SI la autenticación falla después de 3 intentos, ENTONCES EL Script_Refresco DEBERÁ terminar la ejecución y registrar el error

### Requisito 2: Refresco de Datasets

**User Story:** Como analista de datos, quiero refrescar datasets específicos de Power BI, para que los informes muestren información actualizada.

#### Criterios de Aceptación

1. CUANDO se proporciona un identificador de Dataset válido, EL Script_Refresco DEBERÁ iniciar el refresco del Dataset en la Power_BI_API
2. MIENTRAS el refresco está en progreso, EL Script_Refresco DEBERÁ verificar el estado cada 30 segundos
3. CUANDO el refresco se completa exitosamente, EL Script_Refresco DEBERÁ registrar el éxito con timestamp
4. SI el refresco falla, ENTONCES EL Script_Refresco DEBERÁ registrar el mensaje de error proporcionado por la Power_BI_API
5. EL Script_Refresco DEBERÁ soportar el refresco de múltiples Datasets en una sola ejecución

### Requisito 3: Configuración de Workspace

**User Story:** Como administrador de Power BI, quiero especificar qué workspaces contienen los datasets a refrescar, para que el script opere en los espacios correctos.

#### Criterios de Aceptación

1. EL Script_Refresco DEBERÁ aceptar identificadores de Workspace como parámetros de entrada
2. CUANDO se proporciona un identificador de Workspace, EL Script_Refresco DEBERÁ validar que el Service_Principal tiene acceso al Workspace
3. SI el Service_Principal no tiene permisos en el Workspace, ENTONCES EL Script_Refresco DEBERÁ retornar un error descriptivo indicando falta de permisos
4. EL Script_Refresco DEBERÁ listar todos los Datasets disponibles en un Workspace cuando se solicite

### Requisito 4: Registro y Monitoreo

**User Story:** Como administrador de sistemas, quiero que el script registre todas las operaciones y errores, para que pueda monitorear y diagnosticar problemas.

#### Criterios de Aceptación

1. EL Script_Refresco DEBERÁ registrar cada operación con timestamp, nivel de severidad y mensaje descriptivo
2. CUANDO ocurre un error, EL Script_Refresco DEBERÁ registrar el stack trace completo
3. EL Script_Refresco DEBERÁ soportar niveles de logging configurables (DEBUG, INFO, WARNING, ERROR)
4. EL Script_Refresco DEBERÁ escribir logs tanto a consola como a archivo
5. CUANDO un refresco se completa, EL Script_Refresco DEBERÁ registrar el tiempo total de ejecución

### Requisito 5: Documentación de Configuración de Azure

**User Story:** Como administrador de Azure, quiero documentación completa del proceso de configuración de permisos, para que pueda configurar correctamente el service principal y los permisos necesarios.

#### Criterios de Aceptación

1. LA Documentación DEBERÁ incluir los pasos detallados para crear un Service_Principal en Azure AD
2. LA Documentación DEBERÁ incluir los pasos para crear y configurar un Grupo_Seguridad en Azure AD
3. LA Documentación DEBERÁ incluir los pasos para agregar el Service_Principal al Grupo_Seguridad
4. LA Documentación DEBERÁ incluir los pasos para habilitar service principals en la Configuración_Tenant de Power BI
5. LA Documentación DEBERÁ incluir los permisos específicos de API que deben asignarse al Service_Principal
6. LA Documentación DEBERÁ incluir los roles necesarios en cada Workspace de Power BI
7. LA Documentación DEBERÁ incluir comandos de Azure CLI o PowerShell para automatizar la configuración cuando sea posible

### Requisito 6: Manejo de Errores y Reintentos

**User Story:** Como administrador de sistemas, quiero que el script maneje errores transitorios de red, para que los refrescos no fallen por problemas temporales.

#### Criterios de Aceptación

1. CUANDO ocurre un error de red transitorio, EL Script_Refresco DEBERÁ reintentar la operación hasta 3 veces
2. EL Script_Refresco DEBERÁ implementar backoff exponencial entre reintentos (5s, 10s, 20s)
3. SI todos los reintentos fallan, ENTONCES EL Script_Refresco DEBERÁ registrar el error final y continuar con el siguiente Dataset
4. CUANDO la Power_BI_API retorna error de límite de tasa (429), EL Script_Refresco DEBERÁ esperar el tiempo indicado en el header Retry-After

### Requisito 7: Configuración Flexible

**User Story:** Como usuario del script, quiero configurar el comportamiento del script mediante archivo de configuración o parámetros, para que pueda adaptarlo a diferentes entornos.

#### Criterios de Aceptación

1. EL Script_Refresco DEBERÁ soportar configuración mediante archivo JSON o YAML
2. EL Script_Refresco DEBERÁ soportar sobrescritura de configuración mediante argumentos de línea de comandos
3. EL Script_Refresco DEBERÁ validar la configuración al inicio y reportar errores descriptivos si falta información requerida
4. LA Configuración DEBERÁ incluir: credenciales, workspaces, datasets, timeouts, y opciones de logging
5. EL Script_Refresco DEBERÁ proporcionar un archivo de configuración de ejemplo con valores por defecto

### Requisito 8: Compatibilidad con Docker

**User Story:** Como desarrollador, quiero ejecutar el script en un contenedor Docker, para que pueda probarlo en Mac sin instalar dependencias localmente.

#### Criterios de Aceptación

1. EL Proyecto DEBERÁ incluir un Dockerfile que configure el entorno de Python necesario
2. EL Dockerfile DEBERÁ instalar todas las dependencias requeridas del Script_Refresco
3. EL Proyecto DEBERÁ incluir un archivo docker-compose.yml para facilitar la ejecución
4. LA Documentación DEBERÁ incluir instrucciones para construir y ejecutar el contenedor Docker
5. EL Script_Refresco DEBERÁ funcionar correctamente cuando se ejecuta dentro del contenedor Docker

### Requisito 9: Reporte de Estado

**User Story:** Como usuario del script, quiero recibir un resumen al final de la ejecución, para que pueda ver rápidamente qué refrescos tuvieron éxito y cuáles fallaron.

#### Criterios de Aceptación

1. CUANDO el Script_Refresco termina, EL Script_Refresco DEBERÁ mostrar un resumen con el total de Datasets procesados
2. EL Resumen DEBERÁ incluir el número de refrescos exitosos y fallidos
3. EL Resumen DEBERÁ incluir el tiempo total de ejecución
4. PARA CADA Dataset fallido, EL Resumen DEBERÁ mostrar el nombre del Dataset y el motivo del fallo
5. DONDE se configure salida JSON, EL Script_Refresco DEBERÁ generar el resumen en formato JSON estructurado
