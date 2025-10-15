#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a MongoDB
"""
import asyncio
from mongodb_config import mongodb_config

async def test_mongodb_connection():
    print("🔍 Probando conexión a MongoDB...")
    print(f"URL: {mongodb_config.mongodb_url}")
    print(f"Database: {mongodb_config.database_name}")
    
    try:
        await mongodb_config.connect()
        print("✅ MongoDB conectado exitosamente")
        
        # Probar una operación simple
        collection = mongodb_config.get_collection("test")
        result = await collection.insert_one({"test": "connection", "timestamp": "2025-01-15"})
        print(f"✅ Documento de prueba insertado: {result.inserted_id}")
        
        # Limpiar el documento de prueba
        await collection.delete_one({"_id": result.inserted_id})
        print("✅ Documento de prueba eliminado")
        
        await mongodb_config.disconnect()
        print("✅ MongoDB desconectado")
        
    except Exception as e:
        print(f"❌ Error al conectar con MongoDB: {e}")
        print("💡 Verifica que:")
        print("   - La URL de MongoDB sea correcta")
        print("   - Tu IP esté en la lista de acceso de red en MongoDB Atlas")
        print("   - El usuario tenga permisos de lectura y escritura")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())
