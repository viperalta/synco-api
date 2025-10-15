"""
Configuración específica de MongoDB para Vercel
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class VercelMongoDBConfig:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.database_name = os.getenv("MONGODB_DATABASE", "synco_db")
        self.client = None
        self.database = None
        self._connection_lock = None
    
    async def connect(self):
        """Conectar a MongoDB Atlas con configuración optimizada para Vercel"""
        if not self.mongodb_url:
            raise ValueError("MONGODB_URL no está configurada en las variables de entorno")
        
        try:
            # Configuración específica para Vercel/serverless
            self.client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=3000,  # 3 segundos timeout (más rápido)
                connectTimeoutMS=5000,          # 5 segundos para conectar
                socketTimeoutMS=10000,          # 10 segundos para operaciones
                maxPoolSize=5,                  # Pool más pequeño para Vercel
                minPoolSize=0,                  # Sin conexiones mínimas
                maxIdleTimeMS=20000,            # 20 segundos idle
                retryWrites=True,
                retryReads=True,
                # Configuraciones específicas para serverless
                directConnection=False,
                heartbeatFrequencyMS=10000,     # Heartbeat más frecuente
            )
            self.database = self.client[self.database_name]
            
            # Verificar la conexión con timeout más corto
            await self.client.admin.command('ping')
            logger.info(f"Conectado exitosamente a MongoDB Atlas - Base de datos: {self.database_name}")
            
            return True
        except ConnectionFailure as e:
            logger.error(f"Error al conectar con MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al conectar con MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Desconectar de MongoDB"""
        if self.client is not None:
            self.client.close()
            self.client = None
            self.database = None
            logger.info("Desconectado de MongoDB")
    
    def get_collection(self, collection_name: str):
        """Obtener una colección específica"""
        if self.database is None:
            raise ValueError("No hay conexión activa a la base de datos")
        return self.database[collection_name]
    
    async def ensure_connection(self):
        """Asegurar que hay una conexión activa"""
        if self.database is None:
            await self.connect()

# Instancia global de configuración para Vercel
vercel_mongodb_config = VercelMongoDBConfig()
