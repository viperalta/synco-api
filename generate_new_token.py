#!/usr/bin/env python3
"""
Script para generar un nuevo token de Google Calendar con permisos de escritura
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Scopes necesarios para escritura
SCOPES = ['https://www.googleapis.com/auth/calendar']

def generate_new_token():
    """Generar un nuevo token con permisos de escritura"""
    
    print("🔄 Generando nuevo token con permisos de escritura...")
    
    # 1. Obtener credenciales del .env
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_FILE')
    if not credentials_json:
        print("❌ Error: GOOGLE_CREDENTIALS_FILE no encontrada en .env")
        return
    
    # Parsear credenciales
    try:
        credentials_data = json.loads(credentials_json)
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear credenciales: {e}")
        return
    
    # 2. Crear archivo temporal de credenciales
    credentials_file = '/tmp/credentials_temp.json'
    with open(credentials_file, 'w') as f:
        json.dump(credentials_data, f)
    
    print(f"📁 Credenciales guardadas en: {credentials_file}")
    
    # 3. Iniciar flujo de autenticación
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file, SCOPES)
    
    print("🌐 Abriendo navegador para autenticación...")
    print("📋 Asegúrate de autorizar TODOS los permisos solicitados")
    
    # 4. Ejecutar flujo de autenticación
    creds = flow.run_local_server(port=0)
    
    # 5. Crear archivo de token
    token_file = '/tmp/token_new.json'
    with open(token_file, 'w') as f:
        json.dump({
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }, f, indent=2)
    
    print(f"✅ Nuevo token generado: {token_file}")
    
    # 6. Mostrar el contenido del token para copiar al .env
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    print("\n" + "="*80)
    print("📋 COPIA ESTE CONTENIDO A TU VARIABLE GOOGLE_TOKEN_FILE EN .env:")
    print("="*80)
    print(json.dumps(token_data))
    print("="*80)
    
    # 7. Probar el token
    print("\n🧪 Probando el nuevo token...")
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Probar lectura
        events = service.events().list(calendarId='primary', maxResults=1).execute()
        print(f"✅ Lectura exitosa: {len(events.get('items', []))} eventos encontrados")
        
        # Probar escritura (crear un evento de prueba)
        test_event = {
            'summary': '🧪 Test de escritura - ELIMINAR',
            'description': 'Este es un evento de prueba para verificar permisos de escritura',
            'start': {
                'dateTime': '2025-01-01T10:00:00-03:00',
                'timeZone': 'America/Santiago',
            },
            'end': {
                'dateTime': '2025-01-01T11:00:00-03:00',
                'timeZone': 'America/Santiago',
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=test_event).execute()
        print(f"✅ Escritura exitosa: Evento creado con ID {created_event['id']}")
        
        # Eliminar el evento de prueba
        service.events().delete(calendarId='primary', eventId=created_event['id']).execute()
        print("✅ Evento de prueba eliminado")
        
        print("\n🎉 ¡Token generado exitosamente con permisos de escritura!")
        
    except Exception as e:
        print(f"❌ Error al probar el token: {e}")
    
    # 8. Limpiar archivos temporales
    os.remove(credentials_file)
    print(f"\n🧹 Archivos temporales eliminados")
    
    return token_file

if __name__ == "__main__":
    generate_new_token()
