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
            # Configuración optimizada para Vercel/serverless
            self.client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000,  # 5 segundos timeout
                connectTimeoutMS=10000,         # 10 segundos para conectar
                socketTimeoutMS=20000,          # 20 segundos para operaciones
                maxPoolSize=10,                 # Pool de conexiones limitado
                minPoolSize=1,                  # Mínimo 1 conexión
                maxIdleTimeMS=30000,            # 30 segundos idle
                retryWrites=True,
                retryReads=True
            )
            self.database = self.client[self.database_name]
            
            # Verificar la conexión con timeout
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
            # Intentar reconectar si no hay conexión
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                if not loop.is_closed():
                    # Programar reconexión en el event loop
                    asyncio.create_task(self._reconnect())
            except RuntimeError:
                pass
            raise ValueError("No hay conexión activa a la base de datos")
        return self.database[collection_name]
    
    async def _reconnect(self):
        """Intentar reconectar automáticamente"""
        try:
            await self.connect()
            logger.info("Reconectado automáticamente a MongoDB")
        except Exception as e:
            logger.error(f"Error al reconectar automáticamente: {e}")

# Instancia global de configuración
mongodb_config = MongoDBConfig()
