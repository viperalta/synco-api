"""
Servicio para manejar refresh tokens en MongoDB
"""
from typing import Optional
from datetime import datetime, timedelta
from models import RefreshTokenModel
from mongodb_config import mongodb_config
from auth import REFRESH_TOKEN_EXPIRE_DAYS

class RefreshTokenService:
    def __init__(self):
        self.collection_name = "refresh_tokens"
    
    async def get_collection(self):
        """Obtener colección de refresh tokens"""
        return mongodb_config.get_collection(self.collection_name)
    
    async def create_refresh_token(self, user_id: str, token: str) -> RefreshTokenModel:
        """Crear un nuevo refresh token"""
        try:
            collection = await self.get_collection()
            
            # Desactivar tokens anteriores del usuario
            await collection.update_many(
                {"user_id": user_id, "is_active": True},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            # Crear nuevo token
            expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            token_data = {
                "user_id": user_id,
                "token": token,
                "is_active": True,
                "expires_at": expires_at,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.insert_one(token_data)
            token_data["_id"] = result.inserted_id
            
            return RefreshTokenModel(**token_data)
            
        except Exception as e:
            print(f"Error al crear refresh token: {e}")
            raise e
    
    async def get_refresh_token(self, token: str) -> Optional[RefreshTokenModel]:
        """Obtener refresh token por token string"""
        try:
            collection = await self.get_collection()
            token_data = await collection.find_one({
                "token": token,
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if token_data:
                return RefreshTokenModel(**token_data)
            return None
            
        except Exception as e:
            print(f"Error al obtener refresh token: {e}")
            return None
    
    async def revoke_refresh_token(self, token: str) -> bool:
        """Revocar un refresh token"""
        try:
            collection = await self.get_collection()
            result = await collection.update_one(
                {"token": token, "is_active": True},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error al revocar refresh token: {e}")
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """Revocar todos los refresh tokens de un usuario"""
        try:
            collection = await self.get_collection()
            result = await collection.update_many(
                {"user_id": user_id, "is_active": True},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error al revocar todos los tokens del usuario: {e}")
            return False
    
    async def cleanup_expired_tokens(self) -> int:
        """Limpiar tokens expirados"""
        try:
            collection = await self.get_collection()
            result = await collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            return result.deleted_count
            
        except Exception as e:
            print(f"Error al limpiar tokens expirados: {e}")
            return 0

# Instancia global del servicio
refresh_token_service = RefreshTokenService()
