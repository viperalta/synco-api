"""
Configuración de MongoDB para Synco API
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class MongoDBConfig:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.database_name = os.getenv("MONGODB_DATABASE", "synco_db")
        self.client = None
        self.database = None
    
    async def connect(self):
        """Conectar a MongoDB Atlas"""
        if not self.mongodb_url:
            raise ValueError("MONGODB_URL no está configurada en las variables de entorno")
        
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.database = self.client[self.database_name]
            
            # Verificar la conexión
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
            logger.info("Desconectado de MongoDB")
    
    def get_collection(self, collection_name: str):
        """Obtener una colección específica"""
        if self.database is None:
            raise ValueError("No hay conexión activa a la base de datos")
        return self.database[collection_name]

# Instancia global de configuración
mongodb_config = MongoDBConfig()
