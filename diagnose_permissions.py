#!/usr/bin/env python3
"""
Script de diagnóstico para verificar permisos de Power BI.

Este script verifica:
1. Autenticación con Azure AD
2. Permisos de API asignados
3. Acceso a workspaces
4. Configuración del tenant de Power BI
"""

import sys
import os
import requests
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from powerbi_refresh.auth import AuthenticationService
from powerbi_refresh.config import ConfigManager


def print_section(title):
    """Imprime un título de sección."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_authentication(config):
    """Verifica la autenticación con Azure AD."""
    print_section("1. VERIFICANDO AUTENTICACIÓN CON AZURE AD")
    
    try:
        auth_service = AuthenticationService(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret
        )
        
        token = auth_service.get_access_token()
        print("✅ Autenticación exitosa")
        print(f"   Token obtenido (expira en ~1 hora)")
        
        # Decodificar el token para ver los claims (sin verificar firma)
        import base64
        import json
        
        # El token JWT tiene 3 partes separadas por puntos
        parts = token.split('.')
        if len(parts) >= 2:
            # Decodificar el payload (segunda parte)
            payload = parts[1]
            # Agregar padding si es necesario
            padding = len(payload) % 4
            if padding:
                payload += '=' * (4 - padding)
            
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
            
            print(f"   App ID: {claims.get('appid', 'N/A')}")
            print(f"   Tenant ID: {claims.get('tid', 'N/A')}")
            
            # Verificar roles y scopes
            roles = claims.get('roles', [])
            scp = claims.get('scp', '')
            
            if roles:
                print(f"   Roles asignados: {', '.join(roles)}")
            else:
                print("   ⚠️  No se encontraron roles en el token")
            
            if scp:
                print(f"   Scopes: {scp}")
            else:
                print("   ⚠️  No se encontraron scopes en el token")
        
        return True, token
        
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return False, None


def check_api_permissions(token):
    """Verifica los permisos de API consultando Microsoft Graph."""
    print_section("2. VERIFICANDO PERMISOS DE API")
    
    try:
        # Consultar información del service principal
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Intentar acceder a la API de Power BI
        response = requests.get(
            "https://api.powerbi.com/v1.0/myorg/groups",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Acceso a Power BI API exitoso")
            workspaces = response.json().get('value', [])
            print(f"   Workspaces accesibles: {len(workspaces)}")
            
            if workspaces:
                print("\n   Workspaces encontrados:")
                for ws in workspaces[:5]:  # Mostrar solo los primeros 5
                    print(f"     - {ws.get('name')} (ID: {ws.get('id')})")
                if len(workspaces) > 5:
                    print(f"     ... y {len(workspaces) - 5} más")
            else:
                print("   ⚠️  No se encontraron workspaces accesibles")
                print("   Esto puede indicar que el service principal no está")
                print("   agregado a ningún workspace o que los service principals")
                print("   no están habilitados en el tenant.")
            
            return True
            
        elif response.status_code == 401:
            print("❌ Error 401: No autorizado")
            print("   Posibles causas:")
            print("   1. Service principals no habilitados en Power BI Admin Portal")
            print("      Busque: 'Service principals can use Fabric APIs'")
            print("      (Las entidades de servicio pueden llamar a las API públicas de Fabric)")
            print("   2. Permisos de API no asignados correctamente")
            print("   3. Falta consentimiento de administrador para los permisos")
            return False
            
        elif response.status_code == 403:
            print("❌ Error 403: Prohibido")
            print("   El service principal no tiene permisos suficientes")
            return False
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando permisos: {e}")
        return False


def check_workspace_access(token, workspace_id):
    """Verifica el acceso a un workspace específico."""
    print_section(f"3. VERIFICANDO ACCESO AL WORKSPACE")
    
    print(f"   Workspace ID: {workspace_id}")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Intentar listar datasets en el workspace
        response = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            datasets = response.json().get('value', [])
            print(f"✅ Acceso al workspace exitoso")
            print(f"   Datasets encontrados: {len(datasets)}")
            
            if datasets:
                print("\n   Datasets:")
                for ds in datasets:
                    print(f"     - {ds.get('name')} (ID: {ds.get('id')})")
                    print(f"       Refreshable: {ds.get('isRefreshable', 'N/A')}")
            else:
                print("   ⚠️  No se encontraron datasets en este workspace")
            
            return True
            
        elif response.status_code == 401:
            print("❌ Error 401: No autorizado para este workspace")
            print("   Posibles causas:")
            print("   1. Service principal no agregado al workspace")
            print("   2. Service principals no habilitados en el tenant")
            print("   3. Workspace ID incorrecto")
            return False
            
        elif response.status_code == 403:
            print("❌ Error 403: Prohibido")
            print("   El service principal no tiene rol suficiente en el workspace")
            print("   Roles requeridos: Member, Admin, o Contributor")
            return False
            
        elif response.status_code == 404:
            print("❌ Error 404: Workspace no encontrado")
            print("   Verifique que el Workspace ID sea correcto")
            return False
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando workspace: {e}")
        return False


def print_recommendations():
    """Imprime recomendaciones para resolver problemas comunes."""
    print_section("RECOMENDACIONES PARA RESOLVER PROBLEMAS")
    
    print("""
Si el diagnóstico muestra errores, siga estos pasos:

1. HABILITAR SERVICE PRINCIPALS EN POWER BI (MUY IMPORTANTE)
   - Vaya a Power BI Admin Portal (https://app.powerbi.com/admin-portal)
   - Navegue a: Tenant settings > Developer settings
     (Configuración de inquilinos > Configuración de desarrollador)
   - Busque: "Service principals can use Fabric APIs"
     (Las entidades de servicio pueden llamar a las API públicas de Fabric)
   - Nota: En versiones anteriores se llamaba "Allow service principals to use Power BI APIs"
   - Habilite esta opción
   - En "Apply to", seleccione el grupo de seguridad que contiene su service principal
   - Guarde los cambios
   - ⚠️  ESPERE 15-30 MINUTOS para que los cambios se propaguen

2. VERIFICAR PERMISOS DE API EN AZURE AD
   - Vaya a Azure Portal > Azure Active Directory > App registrations
   - Seleccione su aplicación
   - Vaya a "API permissions"
   - Asegúrese de tener estos permisos:
     * Power BI Service > Dataset.Read.All (Application)
     * Power BI Service > Dataset.ReadWrite.All (Application)
   - Haga clic en "Grant admin consent" si no está otorgado
   - ⚠️  ESPERE 5-10 MINUTOS para que los cambios se propaguen

3. AGREGAR SERVICE PRINCIPAL AL WORKSPACE
   - Vaya a Power BI Service (https://app.powerbi.com)
   - Abra el workspace que desea usar
   - Haga clic en "Access" o "Manage access"
   - Agregue el service principal con rol "Member", "Admin", o "Contributor"
   - Busque por el nombre de la aplicación o el App ID

4. VERIFICAR GRUPO DE SEGURIDAD
   - Vaya a Azure Portal > Azure Active Directory > Groups
   - Busque el grupo que configuró en Power BI Admin Portal
   - Verifique que el service principal esté en el grupo
   - Si no está, agréguelo como miembro

5. ESPERAR PROPAGACIÓN
   - Los cambios en Azure AD y Power BI pueden tardar 15-30 minutos
   - Si acaba de hacer cambios, espere y vuelva a ejecutar este diagnóstico

Para más detalles, consulte: docs/azure-setup.md
""")


def main():
    """Función principal del diagnóstico."""
    print("\n" + "=" * 70)
    print("  DIAGNÓSTICO DE PERMISOS DE POWER BI")
    print("=" * 70)
    print("\nEste script verificará la configuración de permisos para el")
    print("service principal de Azure AD usado para refrescar Power BI.")
    
    # Cargar configuración
    try:
        config = ConfigManager.load(config_path="config.yaml")
        print(f"\n✅ Configuración cargada desde config.yaml")
        print(f"   Tenant ID: {config.tenant_id}")
        print(f"   Client ID: {config.client_id}")
        print(f"   Workspaces configurados: {len(config.workspace_ids)}")
    except Exception as e:
        print(f"\n❌ Error cargando configuración: {e}")
        print("\nAsegúrese de tener un archivo config.yaml válido.")
        return 1
    
    # 1. Verificar autenticación
    auth_ok, token = check_authentication(config)
    if not auth_ok:
        print("\n❌ No se pudo autenticar. Verifique las credenciales.")
        return 1
    
    # 2. Verificar permisos de API
    api_ok = check_api_permissions(token)
    
    # 3. Verificar acceso a workspaces
    workspace_ok = True
    for workspace_id in config.workspace_ids:
        if not check_workspace_access(token, workspace_id):
            workspace_ok = False
    
    # Resumen
    print_section("RESUMEN DEL DIAGNÓSTICO")
    
    print(f"\n{'✅' if auth_ok else '❌'} Autenticación con Azure AD")
    print(f"{'✅' if api_ok else '❌'} Acceso a Power BI API")
    print(f"{'✅' if workspace_ok else '❌'} Acceso a workspaces configurados")
    
    if auth_ok and api_ok and workspace_ok:
        print("\n🎉 ¡Todos los permisos están configurados correctamente!")
        print("   El script debería funcionar sin problemas.")
        return 0
    else:
        print("\n⚠️  Se encontraron problemas de configuración.")
        print_recommendations()
        return 1


if __name__ == "__main__":
    sys.exit(main())
