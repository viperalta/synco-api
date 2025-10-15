#!/usr/bin/env python3
"""
Script de ejemplo para configurar el archivo .env
Ejecuta este script después de obtener tus credenciales de Google Cloud Console
"""

import os
import json

def create_env_file():
    """Crea un archivo .env de ejemplo con las variables necesarias"""
    
    print("=== Configuración de Variables de Entorno para Synco API ===\n")
    
    # Verificar si ya existe un archivo .env
    if os.path.exists('.env'):
        response = input("Ya existe un archivo .env. ¿Deseas sobrescribirlo? (y/N): ")
        if response.lower() != 'y':
            print("Operación cancelada.")
            return
    
    print("1. Obtén tus credenciales de Google Cloud Console:")
    print("   - Ve a https://console.cloud.google.com/")
    print("   - Selecciona tu proyecto")
    print("   - Ve a 'APIs & Services' > 'Credentials'")
    print("   - Crea o descarga las credenciales como JSON")
    print()
    
    # Solicitar credenciales
    print("2. Ingresa el contenido JSON de tus credenciales:")
    print("   (Pega todo el contenido del archivo credentials.json)")
    print("   (Presiona Enter en una línea vacía cuando termines)")
    
    credentials_lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        credentials_lines.append(line)
    
    credentials_json = "\n".join(credentials_lines)
    
    # Validar JSON
    try:
        json.loads(credentials_json)
        print("✓ JSON de credenciales válido")
    except json.JSONDecodeError as e:
        print(f"✗ Error: JSON de credenciales inválido: {e}")
        return
    
    print("\n3. Para el token, ejecuta primero:")
    print("   python convert_to_env_format.py")
    print("   (Esto generará el valor GOOGLE_TOKEN_JSON)")
    print()
    
    token_json = input("Ingresa el valor de GOOGLE_TOKEN_JSON: ").strip()
    
    # Validar JSON del token
    try:
        json.loads(token_json)
        print("✓ JSON del token válido")
    except json.JSONDecodeError as e:
        print(f"✗ Error: JSON del token inválido: {e}")
        return
    
    # Crear archivo .env
    env_content = f"""# Google Calendar API Configuration
# OBLIGATORIO: Configura estas variables con el contenido JSON completo

# Credenciales de Google Cloud Console
GOOGLE_CREDENTIALS_JSON={credentials_json}

# Token de autorización (generado después del flujo OAuth)
GOOGLE_TOKEN_JSON={token_json}

# Archivos temporales (generados automáticamente)
GOOGLE_CREDENTIALS_FILE=/tmp/credentials.json
GOOGLE_TOKEN_FILE=/tmp/token.json

# Opcional: ID del calendario por defecto
DEFAULT_CALENDAR_ID=primary
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✓ Archivo .env creado exitosamente!")
    print("\n4. Ahora puedes ejecutar la API:")
    print("   python main.py")
    print("\n5. Para Vercel, copia las variables GOOGLE_CREDENTIALS_JSON y GOOGLE_TOKEN_JSON")
    print("   a la configuración de variables de entorno de tu proyecto.")

if __name__ == "__main__":
    create_env_file()
