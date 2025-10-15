#!/usr/bin/env python3
"""
Script para convertir archivos de credenciales y tokens a formato de variables de entorno
para usar en entornos serverless como Vercel.
"""

import json
import pickle
import base64
import os
from google.oauth2.credentials import Credentials

def convert_credentials_to_env():
    """Convierte credentials.json a formato de variable de entorno"""
    if os.path.exists("credentials.json"):
        with open("credentials.json", "r") as f:
            credentials_data = f.read()
        
        print("GOOGLE_CREDENTIALS_JSON=" + json.dumps(json.loads(credentials_data)))
        print("\nCopia esta línea a tu archivo .env o configuración de Vercel")
    else:
        print("No se encontró credentials.json")

def convert_token_to_env():
    """Convierte token.json (pickle o JSON) a formato de variable de entorno"""
    if os.path.exists("token.json"):
        # Intentar como pickle primero
        try:
            with open("token.json", "rb") as f:
                creds = pickle.load(f)
            
            # Convertir a JSON
            token_json = creds.to_json()
            print("GOOGLE_TOKEN_JSON=" + token_json)
            print("\nCopia esta línea a tu archivo .env o configuración de Vercel")
            
        except Exception:
            # Intentar como JSON
            try:
                with open("token.json", "r") as f:
                    token_data = f.read()
                
                # Validar que es JSON válido
                json.loads(token_data)
                print("GOOGLE_TOKEN_JSON=" + token_data)
                print("\nCopia esta línea a tu archivo .env o configuración de Vercel")
                
            except Exception as e:
                print(f"Error al procesar token.json: {e}")
    else:
        print("No se encontró token.json")

def convert_token_to_base64():
    """Convierte token.json (pickle) a base64 para variable de entorno"""
    if os.path.exists("token.json"):
        try:
            with open("token.json", "rb") as f:
                token_data = f.read()
            
            token_base64 = base64.b64encode(token_data).decode('utf-8')
            print("GOOGLE_TOKEN_BASE64=" + token_base64)
            print("\nCopia esta línea a tu archivo .env o configuración de Vercel")
            
        except Exception as e:
            print(f"Error al procesar token.json: {e}")
    else:
        print("No se encontró token.json")

if __name__ == "__main__":
    print("=== Conversor de archivos a variables de entorno ===\n")
    
    print("1. Credenciales (credentials.json):")
    convert_credentials_to_env()
    
    print("\n" + "="*50 + "\n")
    
    print("2. Token (token.json) - Formato JSON:")
    convert_token_to_env()
    
    print("\n" + "="*50 + "\n")
    
    print("3. Token (token.json) - Formato Base64 (alternativo):")
    convert_token_to_base64()
    
    print("\n" + "="*50 + "\n")
    print("Instrucciones:")
    print("1. Copia las líneas generadas a tu archivo .env")
    print("2. O configura estas variables en tu plataforma de despliegue (Vercel, etc.)")
    print("3. Asegúrate de que el JSON esté en una sola línea sin saltos de línea")
