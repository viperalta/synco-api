"""
Servicio para manejar sesiones con cookies httpOnly
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Response
from models import UserModel
from mongodb_config import mongodb_config

class SessionService:
    def __init__(self):
        self.collection_name = "sessions"
        self.session_cookie_name = "session_token"
        self.session_expire_days = 30
    
    async def get_collection(self):
        """Obtener colección de sesiones"""
        return mongodb_config.get_collection(self.collection_name)
    
    async def create_session(self, user: UserModel) -> str:
        """Crear nueva sesión para un usuario"""
        try:
            collection = await self.get_collection()
            
            # Revocar sesiones existentes del usuario
            await collection.update_many(
                {"user_id": str(user.id), "is_active": True},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            # Crear nueva sesión
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=self.session_expire_days)
            
            session_data = {
                "session_token": session_token,
                "user_id": str(user.id),
                "user_email": user.email,
                "is_active": True,
                "expires_at": expires_at,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await collection.insert_one(session_data)
            return session_token
            
        except Exception as e:
            print(f"Error al crear sesión: {e}")
            raise e
    
    async def get_session(self, session_token: str) -> Optional[UserModel]:
        """Obtener usuario por session token"""
        try:
            collection = await self.get_collection()
            session_data = await collection.find_one({
                "session_token": session_token,
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not session_data:
                return None
            
            # Obtener usuario
            from user_service import user_service
            user = await user_service.get_user_by_email(session_data["user_email"])
            return user
            
        except Exception as e:
            print(f"Error al obtener sesión: {e}")
            return None
    
    async def revoke_session(self, session_token: str) -> bool:
        """Revocar una sesión específica"""
        try:
            collection = await self.get_collection()
            result = await collection.update_one(
                {"session_token": session_token, "is_active": True},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error al revocar sesión: {e}")
            return False
    
    async def revoke_user_sessions(self, user_id: str) -> bool:
        """Revocar todas las sesiones de un usuario"""
        try:
            collection = await self.get_collection()
            result = await collection.update_many(
                {"user_id": user_id, "is_active": True},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error al revocar sesiones del usuario: {e}")
            return False
    
    def set_session_cookie(self, response: Response, session_token: str):
        """Establecer cookie de sesión httpOnly"""
        import os
        
        # Detectar si estamos en desarrollo o producción
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        
        # Determinar el dominio basándose en el entorno
        domain = os.getenv("COOKIE_DOMAIN", ".pasesfalsos.cl")
        
        # En desarrollo, no usar dominio para evitar problemas con localhost
        if not is_production:
            domain = None
        elif domain and not domain.startswith('.'):
            domain = f".{domain}"
        
        print(f"=== DEBUG: Creando cookie con dominio: {domain} ===")
        print(f"=== DEBUG: Nombre de cookie: {self.session_cookie_name} ===")
        print(f"=== DEBUG: Entorno: {'producción' if is_production else 'desarrollo'} ===")
        
        response.set_cookie(
            key=self.session_cookie_name,
            value=session_token,
            max_age=self.session_expire_days * 24 * 60 * 60,  # En segundos
            httponly=True,
            secure=is_production,  # Solo HTTPS en producción
            samesite="lax",  # Compatible con desarrollo y producción
            domain=domain  # Solo en producción
        )
        
        print(f"=== DEBUG: Cookie creada exitosamente ===")
    
    def clear_session_cookie(self, response: Response):
        """Limpiar cookie de sesión"""
        import os
        
        # Determinar el dominio basándose en el entorno
        domain = os.getenv("COOKIE_DOMAIN", ".pasesfalsos.cl")
        
        # Asegurar que el dominio tenga el punto al inicio para subdominios
        if domain and not domain.startswith('.'):
            domain = f".{domain}"
        
        print(f"=== DEBUG: Eliminando cookie con dominio: {domain} ===")
        print(f"=== DEBUG: Nombre de cookie: {self.session_cookie_name} ===")
        
        # Eliminar cookie para el dominio principal
        response.delete_cookie(
            key=self.session_cookie_name,
            domain=domain,
            samesite="lax"
        )
        
        # También eliminar cookie sin dominio (para localhost)
        response.delete_cookie(
            key=self.session_cookie_name,
            samesite="lax"
        )
        
        # En producción, también eliminar para subdominios específicos
        if domain == ".pasesfalsos.cl":
            response.delete_cookie(
                key=self.session_cookie_name,
                domain="api.pasesfalsos.cl",
                samesite="lax"
            )
            response.delete_cookie(
                key=self.session_cookie_name,
                domain="www.pasesfalsos.cl",
                samesite="lax"
            )
        
        print(f"=== DEBUG: Cookie eliminada exitosamente ===")
    
    async def cleanup_expired_sessions(self) -> int:
        """Limpiar sesiones expiradas"""
        try:
            collection = await self.get_collection()
            result = await collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            return result.deleted_count
            
        except Exception as e:
            print(f"Error al limpiar sesiones expiradas: {e}")
            return 0

# Instancia global del servicio
session_service = SessionService()
