# Guía de Configuración de Azure y Power BI

Esta guía proporciona instrucciones detalladas para configurar un service principal de Azure AD con los permisos necesarios para ejecutar el script de refresco de Power BI.

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Crear Service Principal en Azure AD](#crear-service-principal-en-azure-ad)
3. [Crear Grupo de Seguridad](#crear-grupo-de-seguridad)
4. [Agregar Service Principal al Grupo](#agregar-service-principal-al-grupo)
5. [Configurar Permisos de API](#configurar-permisos-de-api)
6. [Habilitar Service Principals en Power BI](#habilitar-service-principals-en-power-bi)
7. [Configurar Roles en Workspaces](#configurar-roles-en-workspaces)
8. [Verificar Configuración](#verificar-configuración)
9. [Solución de Problemas](#solución-de-problemas)

---

## Requisitos Previos

Antes de comenzar, asegúrese de tener:

- **Permisos de Administrador** en Azure Active Directory
- **Permisos de Administrador** en el tenant de Power BI
- **Azure CLI** instalado (opcional, para comandos automatizados)
- **PowerShell** con módulo Az instalado (opcional, para comandos automatizados)

### Instalar Azure CLI (Opcional)

```bash
# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Windows
# Descargar desde: https://aka.ms/installazurecliwindows
```

### Instalar Módulo Az de PowerShell (Opcional)

```powershell
# Instalar módulo Az
Install-Module -Name Az -AllowClobber -Scope CurrentUser

# Conectar a Azure
Connect-AzAccount
```

---

## Crear Service Principal en Azure AD

Un service principal es una identidad de aplicación que permite la autenticación automatizada sin intervención humana.

### Opción 1: Portal de Azure

1. **Navegar a Azure Active Directory**
   - Inicie sesión en [Azure Portal](https://portal.azure.com)
   - Busque y seleccione "Azure Active Directory" / "Microsoft Entra ID"

2. **Registrar Nueva Aplicación**
   - En el menú izquierdo, seleccione "App registrations" / "Registros de aplicaciones"
   - Haga clic en "+ New registration" / "+ Nuevo registro"
   - Configure:
     - **Name** / **Nombre**: `PowerBI-Refresh-ServicePrincipal` (o el nombre que prefiera)
     - **Supported account types** / **Tipos de cuenta admitidos**: "Accounts in this organizational directory only" / "Solo cuentas de este directorio organizativo"
     - **Redirect URI** / **URI de redirección**: Dejar en blanco
   - Haga clic en "Register" / "Registrar"

3. **Anotar Credenciales**
   - En la página de la aplicación, anote:
     - **Application (client) ID** / **Id. de aplicación (cliente)**: Este es su `client_id`
     - **Directory (tenant) ID** / **Id. de directorio (inquilino)**: Este es su `tenant_id`

4. **Crear Client Secret**
   - En el menú izquierdo, seleccione "Certificates & secrets" / "Certificados y secretos"
   - Haga clic en "+ New client secret" / "+ Nuevo secreto de cliente"
   - Configure:
     - **Description** / **Descripción**: `PowerBI-Refresh-Secret`
     - **Expires** / **Expira**: Seleccione la duración apropiada (recomendado: 12-24 meses)
   - Haga clic en "Add" / "Agregar"
   - **IMPORTANTE**: Copie el **Value** / **Valor** inmediatamente. Este es su `client_secret` y no se mostrará nuevamente.

### Opción 2: Azure CLI

```bash
# Iniciar sesión
az login

# Crear service principal
az ad sp create-for-rbac \
  --name "PowerBI-Refresh-ServicePrincipal" \
  --skip-assignment

# Salida esperada:
# {
#   "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",      # client_id
#   "displayName": "PowerBI-Refresh-ServicePrincipal",
#   "password": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",            # client_secret
#   "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"      # tenant_id
# }
```

**IMPORTANTE**: Guarde estas credenciales de forma segura. Se recomienda usar Azure Key Vault o un gestor de secretos.

### Opción 3: PowerShell

```powershell
# Conectar a Azure AD
Connect-AzAccount

# Crear aplicación
$app = New-AzADApplication -DisplayName "PowerBI-Refresh-ServicePrincipal"

# Crear service principal
$sp = New-AzADServicePrincipal -ApplicationId $app.AppId

# Crear client secret
$secret = New-AzADAppCredential -ApplicationId $app.AppId -EndDate (Get-Date).AddMonths(12)

# Mostrar credenciales
Write-Host "Tenant ID: $((Get-AzContext).Tenant.Id)"
Write-Host "Client ID: $($app.AppId)"
Write-Host "Client Secret: $($secret.SecretText)"
```

---

## Crear Grupo de Seguridad

Power BI requiere que los service principals estén en un grupo de seguridad para poder habilitarlos en la configuración del tenant.

### Opción 1: Portal de Azure

1. **Navegar a Azure Active Directory**
   - En [Azure Portal](https://portal.azure.com), vaya a "Azure Active Directory" / "Microsoft Entra ID"

2. **Crear Nuevo Grupo**
   - En el menú izquierdo, seleccione "Groups" / "Grupos"
   - Haga clic en "+ New group" / "+ Nuevo grupo"
   - Configure:
     - **Group type** / **Tipo de grupo**: Security / Seguridad
     - **Group name** / **Nombre del grupo**: `PowerBI-ServicePrincipals`
     - **Group description** / **Descripción del grupo**: "Grupo de seguridad para service principals con acceso a Power BI"
     - **Membership type** / **Tipo de pertenencia**: Assigned / Asignado
   - Haga clic en "Create" / "Crear"

3. **Anotar Object ID**
   - Abra el grupo recién creado
   - Anote el **Object ID** / **Id. de objeto** del grupo (lo necesitará más adelante)

### Opción 2: Azure CLI

```bash
# Crear grupo de seguridad
az ad group create \
  --display-name "PowerBI-ServicePrincipals" \
  --mail-nickname "PowerBI-ServicePrincipals" \
  --description "Grupo de seguridad para service principals con acceso a Power BI"

# Obtener Object ID del grupo
az ad group show \
  --group "PowerBI-ServicePrincipals" \
  --query objectId \
  --output tsv
```

### Opción 3: PowerShell

```powershell
# Crear grupo de seguridad
$group = New-AzADGroup `
  -DisplayName "PowerBI-ServicePrincipals" `
  -MailNickname "PowerBI-ServicePrincipals" `
  -Description "Grupo de seguridad para service principals con acceso a Power BI"

# Mostrar Object ID
Write-Host "Group Object ID: $($group.Id)"
```

---

## Agregar Service Principal al Grupo

Ahora debe agregar el service principal al grupo de seguridad.

### Opción 1: Portal de Azure

1. **Abrir el Grupo**
   - En Azure Active Directory > Groups / Grupos
   - Seleccione el grupo "PowerBI-ServicePrincipals"

2. **Agregar Miembro**
   - En el menú izquierdo, seleccione "Members" / "Miembros"
   - Haga clic en "+ Add members" / "+ Agregar miembros"
   - Busque el nombre de su service principal: `PowerBI-Refresh-ServicePrincipal`
   - Selecciónelo y haga clic en "Select" / "Seleccionar"

### Opción 2: Azure CLI

```bash
# Obtener Object ID del service principal
SP_OBJECT_ID=$(az ad sp list \
  --display-name "PowerBI-Refresh-ServicePrincipal" \
  --query "[0].objectId" \
  --output tsv)

# Obtener Object ID del grupo
GROUP_OBJECT_ID=$(az ad group show \
  --group "PowerBI-ServicePrincipals" \
  --query objectId \
  --output tsv)

# Agregar service principal al grupo
az ad group member add \
  --group $GROUP_OBJECT_ID \
  --member-id $SP_OBJECT_ID

# Verificar membresía
az ad group member list \
  --group "PowerBI-ServicePrincipals" \
  --query "[].displayName"
```

### Opción 3: PowerShell

```powershell
# Obtener service principal
$sp = Get-AzADServicePrincipal -DisplayName "PowerBI-Refresh-ServicePrincipal"

# Obtener grupo
$group = Get-AzADGroup -DisplayName "PowerBI-ServicePrincipals"

# Agregar service principal al grupo
Add-AzADGroupMember -TargetGroupObjectId $group.Id -MemberObjectId $sp.Id

# Verificar membresía
Get-AzADGroupMember -GroupObjectId $group.Id | Select-Object DisplayName
```

---

## Configurar Permisos de API

El service principal necesita permisos específicos de la API de Power BI.

### Opción 1: Portal de Azure

1. **Navegar a la Aplicación**
   - En Azure Active Directory > App registrations / Registros de aplicaciones
   - Seleccione su aplicación "PowerBI-Refresh-ServicePrincipal"

2. **Agregar Permisos de API**
   - En el menú izquierdo, seleccione "API permissions" / "Permisos de API"
   - Haga clic en "+ Add a permission" / "+ Agregar un permiso"
   - Seleccione "Power BI Service" / "Servicio Power BI"
   - Seleccione "Delegated permissions" / "Permisos delegados"
   - Marque los siguientes permisos:
     - `Dataset.Read.All` - Leer todos los datasets
     - `Dataset.ReadWrite.All` - Leer y escribir todos los datasets
   - Haga clic en "Add permissions" / "Agregar permisos"

3. **Otorgar Consentimiento de Administrador**
   - En la página "API permissions" / "Permisos de API"
   - Haga clic en "Grant admin consent for [Your Organization]" / "Conceder consentimiento de administrador para [Su Organización]"
   - Confirme haciendo clic en "Yes" / "Sí"
   - Verifique que el estado muestre "Granted for [Your Organization]" / "Concedido para [Su Organización]"

### Opción 2: Azure CLI

```bash
# Obtener Application ID
APP_ID=$(az ad app list \
  --display-name "PowerBI-Refresh-ServicePrincipal" \
  --query "[0].appId" \
  --output tsv)

# Obtener Service Principal ID de Power BI
POWERBI_SP_ID=$(az ad sp list \
  --filter "displayName eq 'Power BI Service'" \
  --query "[0].appId" \
  --output tsv)

# Agregar permisos (requiere Microsoft Graph API)
# Nota: Este comando puede requerir permisos adicionales
az ad app permission add \
  --id $APP_ID \
  --api $POWERBI_SP_ID \
  --api-permissions \
    "Dataset.Read.All=Scope" \
    "Dataset.ReadWrite.All=Scope"

# Otorgar consentimiento de administrador
az ad app permission admin-consent --id $APP_ID
```

### Opción 3: PowerShell

```powershell
# Obtener aplicación
$app = Get-AzADApplication -DisplayName "PowerBI-Refresh-ServicePrincipal"

# Nota: La configuración de permisos de API mediante PowerShell
# es compleja y se recomienda usar el Portal de Azure o Azure CLI
# para esta tarea específica.

Write-Host "Por favor, configure los permisos de API manualmente en el Portal de Azure:"
Write-Host "1. Vaya a Azure AD > App registrations > $($app.DisplayName)"
Write-Host "2. Seleccione 'API permissions'"
Write-Host "3. Agregue permisos de Power BI Service"
```

### Permisos Requeridos

| Permiso | Tipo | Descripción | Requerido |
|---------|------|-------------|-----------|
| `Dataset.Read.All` | Delegated | Leer todos los datasets | Sí |
| `Dataset.ReadWrite.All` | Delegated | Leer y escribir todos los datasets | Sí |

**Nota**: Los permisos "Delegated" son suficientes para este caso de uso. Los permisos "Application" no son necesarios.

---

## Habilitar Service Principals en Power BI

Power BI debe configurarse para permitir que los service principals accedan a la API.

### Pasos en el Portal de Power BI

1. **Acceder al Portal de Administración**
   - Inicie sesión en [Power BI Service](https://app.powerbi.com)
   - Haga clic en el ícono de engranaje (⚙️) en la esquina superior derecha
   - Seleccione "Admin portal" / "Portal de administración"

2. **Configurar Tenant Settings**
   - En el menú izquierdo, seleccione "Tenant settings" / "Configuración de inquilinos"
   - Desplácese hasta la sección "Developer settings" / "Configuración de desarrollador"

3. **Habilitar Service Principals**
   - Busque la configuración "Service principals can use Fabric APIs" / "Las entidades de servicio pueden llamar a las API públicas de Fabric"
   - **Nota**: En versiones anteriores esta opción se llamaba "Allow service principals to use Power BI APIs" / "Permitir que las entidades de servicio usen las API de Power BI"
   - Habilite el toggle / Habilite el conmutador
   - Seleccione "Specific security groups" / "Grupos de seguridad específicos"
   - Haga clic en "Add security groups" / "Agregar grupos de seguridad"
   - Busque y agregue el grupo "PowerBI-ServicePrincipals"
   - Haga clic en "Apply" / "Aplicar"

4. **Habilitar Acceso a Workspaces (Opcional pero Recomendado)**
   - Busque la configuración "Service principals can access read-only admin APIs" / "Las entidades de servicio pueden acceder a las API de administración de solo lectura"
   - Habilite el toggle / Habilite el conmutador
   - Seleccione "Specific security groups" / "Grupos de seguridad específicos"
   - Agregue el grupo "PowerBI-ServicePrincipals"
   - Haga clic en "Apply" / "Aplicar"

### Configuraciones Adicionales Recomendadas

| Configuración | Ubicación | Recomendación |
|---------------|-----------|---------------|
| Service principals can use Fabric APIs / Las entidades de servicio pueden llamar a las API públicas de Fabric | Developer settings / Configuración de desarrollador | Habilitado para grupo específico |
| Service principals can access read-only admin APIs / Las entidades de servicio pueden acceder a las API de administración de solo lectura | Admin API settings / Configuración de API de administración | Habilitado para grupo específico |

**Nota**: La configuración "Service principals can use Fabric APIs" reemplazó a la antigua "Allow service principals to use Power BI APIs" con la integración de Microsoft Fabric.

### Verificar Configuración

```bash
# No hay comando CLI directo para verificar esta configuración
# Debe verificarse manualmente en el Portal de Power BI
```

**IMPORTANTE**: Los cambios en la configuración del tenant pueden tardar hasta 15 minutos en propagarse.

---

## Configurar Roles en Workspaces

El service principal debe tener permisos adecuados en cada workspace que contenga datasets a refrescar.

### Roles Disponibles

| Rol | Permisos | Puede Refrescar Datasets |
|-----|----------|--------------------------|
| **Admin** | Control total del workspace | ✅ Sí |
| **Member** | Editar contenido, refrescar datasets | ✅ Sí |
| **Contributor** | Crear y editar contenido | ✅ Sí |
| **Viewer** | Solo lectura | ❌ No |

**Recomendación**: Use el rol **Member** o **Contributor** para el service principal.

### Opción 1: Portal de Power BI

1. **Abrir el Workspace**
   - En [Power BI Service](https://app.powerbi.com)
   - Navegue al workspace que contiene los datasets

2. **Acceder a Configuración**
   - Haga clic en "..." (más opciones) junto al nombre del workspace
   - Seleccione "Workspace access" / "Acceso al área de trabajo"

3. **Agregar Service Principal**
   - Haga clic en "+ Add" / "+ Agregar"
   - En el campo de búsqueda, ingrese el nombre del service principal: `PowerBI-Refresh-ServicePrincipal`
   - Seleccione el service principal de la lista
   - Seleccione el rol: **Member** / **Miembro** o **Contributor** / **Colaborador**
   - Haga clic en "Add" / "Agregar"

### Opción 2: PowerShell con Power BI Management Module

```powershell
# Instalar módulo de Power BI (si no está instalado)
Install-Module -Name MicrosoftPowerBIMgmt -Scope CurrentUser

# Conectar a Power BI
Connect-PowerBIServiceAccount

# Obtener service principal
$sp = Get-AzADServicePrincipal -DisplayName "PowerBI-Refresh-ServicePrincipal"

# Agregar service principal al workspace
Add-PowerBIWorkspaceUser `
  -Scope Organization `
  -Id "WORKSPACE-GUID-AQUI" `
  -UserPrincipalName $sp.AppId `
  -AccessRight Member `
  -PrincipalType App

# Verificar acceso
Get-PowerBIWorkspaceUser -Scope Organization -Id "WORKSPACE-GUID-AQUI"
```

### Opción 3: API REST de Power BI

```bash
# Obtener token de acceso (requiere permisos de administrador)
ACCESS_TOKEN="your-admin-access-token"
WORKSPACE_ID="your-workspace-id"
SP_OBJECT_ID="your-service-principal-object-id"

# Agregar service principal al workspace
curl -X POST \
  "https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/users" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "'${SP_OBJECT_ID}'",
    "groupUserAccessRight": "Member",
    "principalType": "App"
  }'
```

### Configurar Múltiples Workspaces

Si necesita configurar el service principal en múltiples workspaces:

```powershell
# Lista de workspace IDs
$workspaceIds = @(
    "workspace-guid-1",
    "workspace-guid-2",
    "workspace-guid-3"
)

# Service principal
$sp = Get-AzADServicePrincipal -DisplayName "PowerBI-Refresh-ServicePrincipal"

# Agregar a todos los workspaces
foreach ($workspaceId in $workspaceIds) {
    try {
        Add-PowerBIWorkspaceUser `
            -Scope Organization `
            -Id $workspaceId `
            -UserPrincipalName $sp.AppId `
            -AccessRight Member `
            -PrincipalType App
        Write-Host "✓ Agregado a workspace: $workspaceId"
    }
    catch {
        Write-Host "✗ Error en workspace $workspaceId : $_"
    }
}
```

---

## Verificar Configuración

Después de completar todos los pasos, verifique que la configuración sea correcta.

### Checklist de Verificación

- [ ] Service principal creado en Azure AD
- [ ] Client ID, Tenant ID y Client Secret anotados de forma segura
- [ ] Grupo de seguridad "PowerBI-ServicePrincipals" creado
- [ ] Service principal agregado al grupo de seguridad
- [ ] Permisos de API configurados (Dataset.Read.All, Dataset.ReadWrite.All)
- [ ] Consentimiento de administrador otorgado para los permisos
- [ ] Service principals habilitados en Power BI tenant settings
- [ ] Service principal agregado a workspaces con rol Member o Contributor
- [ ] Esperado 15 minutos para propagación de cambios

### Script de Verificación

Cree un archivo `verify_setup.py` para probar la configuración:

```python
import os
import requests
from msal import ConfidentialClientApplication

# Credenciales (usar variables de entorno en producción)
TENANT_ID = "your-tenant-id"
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"

# Autenticar
authority = f"https://login.microsoftonline.com/{TENANT_ID}"
app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=authority,
    client_credential=CLIENT_SECRET
)

# Obtener token
result = app.acquire_token_for_client(
    scopes=["https://analysis.windows.net/powerbi/api/.default"]
)

if "access_token" in result:
    print("✓ Autenticación exitosa")
    token = result["access_token"]
    
    # Probar acceso a API
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "https://api.powerbi.com/v1.0/myorg/groups",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ Acceso a Power BI API exitoso")
        workspaces = response.json()["value"]
        print(f"✓ Workspaces accesibles: {len(workspaces)}")
        for ws in workspaces:
            print(f"  - {ws['name']} ({ws['id']})")
    else:
        print(f"✗ Error al acceder a API: {response.status_code}")
        print(f"  {response.text}")
else:
    print("✗ Error de autenticación:")
    print(f"  {result.get('error')}: {result.get('error_description')}")
```

Ejecutar el script:

```bash
python verify_setup.py
```

### Salida Esperada

```
✓ Autenticación exitosa
✓ Acceso a Power BI API exitoso
✓ Workspaces accesibles: 3
  - Sales Analytics (abc-123-def-456)
  - Marketing Reports (ghi-789-jkl-012)
  - Finance Dashboard (mno-345-pqr-678)
```

---

## Solución de Problemas

### Error: "AADSTS7000215: Invalid client secret is provided"

**Causa**: El client secret es incorrecto o ha expirado.

**Solución**:
1. Vaya a Azure AD > App registrations / Registros de aplicaciones > Su aplicación
2. Seleccione "Certificates & secrets" / "Certificados y secretos"
3. Cree un nuevo client secret
4. Actualice la configuración con el nuevo secret

### Error: "Unauthorized - 401"

**Causa**: El service principal no tiene permisos en el workspace o los permisos de API no están configurados.

**Solución**:
1. Verifique que el service principal esté agregado al workspace con rol Member / Miembro o Contributor / Colaborador
2. Verifique que los permisos de API estén configurados y el consentimiento de administrador esté otorgado
3. Espere 15 minutos para que los cambios se propaguen

### Error: "Service principals are not enabled"

**Causa**: Los service principals no están habilitados en la configuración del tenant de Power BI.

**Solución**:
1. Vaya a Power BI Admin portal / Portal de administración > Tenant settings / Configuración de inquilinos
2. Habilite "Service principals can use Fabric APIs" / "Las entidades de servicio pueden llamar a las API públicas de Fabric"
   - **Nota**: En versiones anteriores se llamaba "Allow service principals to use Power BI APIs"
3. Agregue el grupo de seguridad que contiene el service principal
4. Espere 15 minutos para que los cambios se propaguen

### Error: "The specified group was not found"

**Causa**: El grupo de seguridad no existe o el service principal no está en el grupo.

**Solución**:
1. Verifique que el grupo "PowerBI-ServicePrincipals" existe en Azure AD
2. Verifique que el service principal es miembro del grupo
3. Use los comandos de verificación de membresía proporcionados anteriormente

### Error: "Refresh failed - Dataset not found"

**Causa**: El dataset ID es incorrecto o el service principal no tiene acceso al workspace.

**Solución**:
1. Verifique el dataset ID en Power BI Service
2. Verifique que el service principal tiene acceso al workspace
3. Verifique que el dataset es refrescable (no es un dataset de streaming)

### Error: "Token acquisition failed"

**Causa**: Problema con las credenciales o la configuración de Azure AD.

**Solución**:
1. Verifique que tenant_id, client_id y client_secret son correctos
2. Verifique que el service principal no ha sido eliminado
3. Verifique que el client secret no ha expirado
4. Intente crear un nuevo client secret

### Logs de Diagnóstico

Para obtener más información sobre errores, habilite logging detallado:

```bash
# Ejecutar script con logging DEBUG
python -m powerbi_refresh.main \
  --config config.yaml \
  --log-level DEBUG \
  --log-file debug.log
```

Revise el archivo `debug.log` para información detallada sobre el error.

---

## Recursos Adicionales

### Documentación Oficial

- [Azure AD Service Principals](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
- [Power BI REST API](https://docs.microsoft.com/en-us/rest/api/power-bi/)
- [Power BI Service Principal](https://docs.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)

### Herramientas Útiles

- [Azure Portal](https://portal.azure.com)
- [Power BI Service](https://app.powerbi.com)
- [Microsoft Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) - Para probar llamadas a API

### Seguridad y Mejores Prácticas

1. **Gestión de Secretos**
   - Use Azure Key Vault para almacenar credenciales
   - Rote los client secrets regularmente (cada 6-12 meses)
   - No almacene secretos en código fuente o repositorios

2. **Principio de Menor Privilegio**
   - Otorgue solo los permisos mínimos necesarios
   - Use grupos de seguridad específicos, no "Entire organization"
   - Revise permisos regularmente

3. **Auditoría y Monitoreo**
   - Habilite logging de auditoría en Azure AD
   - Monitoree el uso del service principal
   - Configure alertas para actividad inusual

4. **Documentación**
   - Documente qué service principals existen y su propósito
   - Documente quién tiene acceso a las credenciales
   - Mantenga un inventario de workspaces y permisos

---

## Resumen de Comandos Rápidos

### Crear Todo con Azure CLI

```bash
# 1. Crear service principal
az ad sp create-for-rbac --name "PowerBI-Refresh-ServicePrincipal" --skip-assignment

# 2. Crear grupo de seguridad
az ad group create --display-name "PowerBI-ServicePrincipals" --mail-nickname "PowerBI-ServicePrincipals"

# 3. Agregar service principal al grupo
SP_ID=$(az ad sp list --display-name "PowerBI-Refresh-ServicePrincipal" --query "[0].objectId" -o tsv)
GROUP_ID=$(az ad group show --group "PowerBI-ServicePrincipals" --query objectId -o tsv)
az ad group member add --group $GROUP_ID --member-id $SP_ID

# 4. Configurar permisos de API (requiere portal)
echo "Configure API permissions manually in Azure Portal"

# 5. Habilitar en Power BI (requiere portal)
echo "Enable service principals in Power BI Admin Portal"

# 6. Agregar a workspaces (requiere PowerShell o portal)
echo "Add service principal to workspaces in Power BI Service"
```

### Crear Todo con PowerShell

```powershell
# 1. Conectar
Connect-AzAccount

# 2. Crear aplicación y service principal
$app = New-AzADApplication -DisplayName "PowerBI-Refresh-ServicePrincipal"
$sp = New-AzADServicePrincipal -ApplicationId $app.AppId
$secret = New-AzADAppCredential -ApplicationId $app.AppId -EndDate (Get-Date).AddMonths(12)

# 3. Crear grupo
$group = New-AzADGroup -DisplayName "PowerBI-ServicePrincipals" -MailNickname "PowerBI-ServicePrincipals"

# 4. Agregar al grupo
Add-AzADGroupMember -TargetGroupObjectId $group.Id -MemberObjectId $sp.Id

# 5. Mostrar credenciales
Write-Host "Tenant ID: $((Get-AzContext).Tenant.Id)"
Write-Host "Client ID: $($app.AppId)"
Write-Host "Client Secret: $($secret.SecretText)"

# 6. Configurar permisos de API (requiere portal)
Write-Host "Configure API permissions manually in Azure Portal"

# 7. Habilitar en Power BI (requiere portal)
Write-Host "Enable service principals in Power BI Admin Portal"

# 8. Agregar a workspaces
Connect-PowerBIServiceAccount
Add-PowerBIWorkspaceUser -Scope Organization -Id "WORKSPACE-ID" -UserPrincipalName $sp.AppId -AccessRight Member -PrincipalType App
```

---

**Última actualización**: 2024
**Versión del documento**: 1.0
